"""Queue on the normal publication lock using the same guarded connection."""
def queueing_factory(original,expected_target):
 def construct(env_path,writable=False,public_url=None):
  store=original(env_path,False,public_url)
  if writable:
   try:
    assert store.target_fingerprint==expected_target,'Reviewed MySQL target changed'
    with store.connection.cursor() as cursor:
     cursor.execute("SELECT GET_LOCK('histree-content-publish',30)")
     assert cursor.fetchone()[0]==1,'Publication queue timed out; no write capability enabled'
    store.writable=True
   except BaseException:
    store.connection.close();raise
  return store
 return construct
def install(expected_target):
 import mysql_content_store
 mysql_content_store.MysqlContentStore=queueing_factory(mysql_content_store.MysqlContentStore,expected_target)
