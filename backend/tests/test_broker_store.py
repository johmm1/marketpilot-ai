import os
import sqlite3
import tempfile
import unittest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from backend.app import broker_store, db


class BrokerStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        db.DB_PATH=os.path.join(self.temp.name,"test.db")
        broker_store.settings.broker_encryption_key=Fernet.generate_key().decode()
        with sqlite3.connect(broker_store.DB_PATH) as db:
            db.execute("CREATE TABLE users (id TEXT PRIMARY KEY)")
            db.execute("INSERT INTO users(id) VALUES ('user-a')")
            db.execute("INSERT INTO users(id) VALUES ('user-b')")
        broker_store.initialize_broker_store()

    def tearDown(self):
        broker_store.settings.broker_encryption_key=""
        self.temp.cleanup()

    def test_credentials_are_encrypted_and_user_scoped(self):
        broker_store.save_connection("user-a","binance","test","testnet",
                                     {"api_key":"key-value","api_secret":"secret-value"})
        saved=broker_store.get_connection("user-a","binance")
        self.assertEqual(saved["secrets"]["api_secret"],"secret-value")
        with self.assertRaises(HTTPException):
            broker_store.get_connection("user-b","binance")
        listed=broker_store.list_connections("user-a")
        self.assertEqual(len(listed),1)
        self.assertNotIn("secret-value",str(listed))

    def test_oauth_state_is_single_use_and_user_bound(self):
        state=broker_store.create_oauth_state("user-a","ctrader")
        self.assertEqual(broker_store.consume_oauth_state(state,"ctrader"),"user-a")
        with self.assertRaises(HTTPException):
            broker_store.consume_oauth_state(state,"ctrader")

    def test_mt5_token_rotation_and_disconnect_revoke_access(self):
        first=broker_store.create_mt5_bridge_token("user-a")
        self.assertEqual(broker_store.verify_mt5_bridge_token(first),"user-a")
        second=broker_store.create_mt5_bridge_token("user-a")
        with self.assertRaises(HTTPException):
            broker_store.verify_mt5_bridge_token(first)
        broker_store.save_connection("user-a","metatrader5","Windows MT5 bridge","read_only",{"snapshot":{}})
        mt5=next(item for item in broker_store.list_connections("user-a") if item["provider"]=="metatrader5")\n        broker_store.delete_connection("user-a",mt5["id"])
        with self.assertRaises(HTTPException):
            broker_store.verify_mt5_bridge_token(second)


if __name__=="__main__":
    unittest.main()
