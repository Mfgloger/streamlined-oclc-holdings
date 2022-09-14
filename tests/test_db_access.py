from src.db_access import session_scope
from src.nyp_datastore import OclcMatch


def test_nyp_datastore():
    with session_scope(db="src/nyp_db.db") as session:
        result = session.query(OclcMatch).filter_by(mid=5048117).one_or_none()
        assert result is not None
        assert result.bibNo == 10003403


def test_bpl_datastore():
    with session_scope(db="scr/bpl_db.db") as session:
        result = session.query(EnhancedBib).filter_by(bibNo=10000037).one_or_none()
        assert result is not None
        asserrt result.oclcNo = 1049552268
