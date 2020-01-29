import logging
import threading
import time
import uuid

import pytest
from sqlalchemy import create_engine, inspect, Column, ForeignKey, Integer, String, true
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from testing_support import PropagatingThread


log = logging.getLogger(__name__)


Base = declarative_base()


class Thing(Base):
    __tablename__ = 'things'

    id = Column(Integer, primary_key=True)
    status = Column(String)

    aughts = relationship('Aught', backref='thing')


class Aught(Base):
    __tablename__ = 'aughts'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    thing_id = Column(Integer, ForeignKey('things.id'))


class UuidThing(Base):
    __tablename__ = 'uuid_things'

    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


@pytest.fixture(scope='session')
def engine():
    # engine = create_engine('sqlite:///')
    engine = create_engine('postgresql+psycopg2://spikes-python3:sesame@localhost/spikes-python3')
    Base.metadata.create_all(engine)

    yield engine

    Base.metadata.drop_all(engine)


@pytest.fixture
def connection(engine):
    with engine.connect() as conn:
        transaction = conn.begin()

        yield conn

        transaction.rollback()


@pytest.fixture
def make_db(connection):
    factory = sessionmaker(bind=connection)

    yield factory

    factory.close_all()


@pytest.fixture
def db(make_db):
    yield make_db()


# @pytest.mark.skip
def test_select_for_update(engine):
    make_db = sessionmaker(bind=engine)
    # scoped_db = scoped_session(sessionmaker(bind=engine))
    db = make_db()
    thing = Thing(status='old')
    db.add(thing)
    db.commit()

    def first(event, sess_factory, t_id, status):
        sess = sess_factory()
        # thing = sess.query(Thing).get(1)
        thing = sess.query(Thing).with_for_update().get(t_id)
        event.set()  # poke second thread
        log.debug('Make him wait for a while')
        time.sleep(0.263)
        thing.status = status
        sess.commit()
        log.debug('Done!')
        # sess_factory.remove()

    def second(event, sess_factory, t_id, status):
        event.wait()  # ensure we are called in the right moment
        sess = sess_factory()
        # thing = sess.query(Thing).get(1)
        thing = sess.query(Thing).with_for_update().get(t_id)
        thing.status = status
        sess.commit()
        log.debug('Oy! I must come last...')
        # sess_factory.remove()

    event = threading.Event()
    th1 = PropagatingThread(target=first, args=(event, make_db, thing.id, 'new'))
    th2 = PropagatingThread(target=second, args=(event, make_db, thing.id, 'brand_new'))

    th1.start()
    th2.start()

    th1.join()
    th2.join()

    db.refresh(thing)
    assert thing.status == 'brand_new'


@pytest.mark.skip
def test_reproducing_alchemy_error(db):
    # causing error
    db.query(Thing).filter_by(non_existing_field='spam')

    # now session's transcation must be relled back in order to use it again
    db.query(Thing).get(1)


def test_orm_expire_in_other_session(make_db):
    db = make_db()
    thing = Thing()
    db.add(thing)
    db.commit()  # expired

    another_db = make_db()
    same_thing = another_db.query(Thing).get(thing.id)
    same_thing.status = 'updated_in_other_session'
    another_db.commit()

    db.refresh(thing)  # must refresh to get updated data
    assert thing.status == 'updated_in_other_session'


def test_instances_equallity(make_db):
    db = make_db()
    thing = Thing()
    db.add(thing)
    db.commit()

    another_db = make_db()
    another_thing = another_db.query(Thing).get(thing.id)

    assert another_thing.id == thing.id


def test_scalar(db):
    db.add(Thing())
    db.commit()

    res = db.query(true()).one()

    assert res == (True,)

    # doing it right
    res = db.query(true()).scalar()

    assert res is True


def test_commiting_relationship(db):
    thing = Thing()
    db.add(thing)
    db.commit()

    aughts = [Aught(name='foo'), Aught(name='bar')]

    thing.aughts = aughts
    db.commit()

    assert db.query(Thing).get(thing.id).aughts == aughts


def test_thing_with_uuid_primary_key(db):
    thing = UuidThing()

    db.add(thing)
    db.commit()

    assert thing.uid

    thing = db.query(UuidThing).get(thing.uid)

    assert type(thing.uid) is uuid.UUID
