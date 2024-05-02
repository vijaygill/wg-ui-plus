from flask import Flask,send_from_directory
import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import select

class Base(DeclarativeBase):
    pass

class Peer(Base):
    __tablename__ = "wg_peers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    device_name:  Mapped[str] = mapped_column(String(255))

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.device_name!r})"

class DbRepo(object):
    def __init__(self, engine):
        self.engine = engine

    def createSampleData(self):
        with Session(self.engine) as session:
            for i in range(0,10):
                peer = Peer(name = f'Peer - {i}', device_name = f'Device - {i}')
                session.add(peer)
                session.commit()

    def getPeers(self):
        self.createSampleData()
        with Session(self.engine) as session:
            res = [ { "name": c.name } for c in session.query( Peer ).all() ]
            return res

engine = create_engine("sqlite:///./data/wg-ui-plus.db", echo = True)
Base.metadata.create_all(engine)
#db = DbRepo(engine)
#db.createSampleData()

USE_SSR = False # Will get SSR working some other time

BASE_DIR_INFOS = [
        ('wg-ui-plus/dist/wg-ui-plus/browser', 'index.html'),
        ('wg-ui-plus/dist/wg-ui-plus/server', 'index.server.html'),
        ]

BASE_DIR_INFO = BASE_DIR_INFOS[1] if USE_SSR else BASE_DIR_INFOS[0]

BASE_DIR, INDEX_RESOURCE = BASE_DIR_INFO

app = Flask(__name__, static_folder = BASE_DIR,  )
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['EXPLAIN_TEMPLATE_LOADING'] = False

@app.route('/<path:path>', methods=['GET'])
def serve_static_files(path):
    app.logger.info(f'serve_static_files: {path}')
    return send_from_directory(BASE_DIR, path)

@app.route('/test')
def test():
    app.logger.info(f'test')
    return 'Hello, World!'

@app.route('/peers')
def peers():
    app.logger.info(f'returning list of peers')
    db = DbRepo(engine)
    peers = db.getPeers()
    app.logger.info(f'***** {peers} ')
    return peers


@app.route('/')
def index():
    app.logger.info(f'index')
    return app.send_static_file(INDEX_RESOURCE)

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 80)
