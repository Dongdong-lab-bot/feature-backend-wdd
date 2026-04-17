from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict

from paho.mqtt.client import Client, MQTTMessage

from app.core.config import settings
from app.db import sync_db_session
from app.modules.device.models import BizDevice, BizDeviceRecord

logger = logging.getLogger(__name__)

DATA_TYPE_AI_BOX_CODE = "AI_BOX_RECORD"
SOURCE_DEVICE_AUTO = "DEVICE_AUTO"
PROCESS_RESULT_SUCCESS = "SUCCESS"

def _init_mqtt_client() -> Client:
    client = Client(client_id=settings.mqtt_client_id)
    if settings.mqtt_username and settings.mqtt_password:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    return client

mqtt_client = _init_mqtt_client()

def on_connect(client: Client, userdata: Any, flags: Any, rc: int) -> None:
    if rc == 0:
        logger.info(f"Connected to MQTT Broker: {settings.mqtt_broker}")
        client.subscribe(settings.mqtt_topic)
    else:
        logger.error(f"Failed to connect to MQTT Broker, return code {rc}")

def on_message(client: Client, userdata: Any, msg: MQTTMessage) -> None:
    try:
        payload_str = msg.payload.decode("utf-8")
        payload = json.loads(payload_str)
        operator = payload.get("operator")
        if operator != "RecordPush":
            return
            
        info = payload.get("info", {})
        aibox_id = info.get("aibox_id")
        if not aibox_id:
            logger.warning("Empty aibox_id in MQTT message")
            return
            
        time_str = info.get("time")
        try:
            submit_date = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").date()
        except BaseException:
            from datetime import timezone
            submit_date = datetime.now(timezone.utc).date()

        with sync_db_session() as db:
            device = db.query(BizDevice).filter(BizDevice.device_code == aibox_id).first()
            if not device:
                logger.warning(f"Device not found with code: {aibox_id}")
                return
            
            record = BizDeviceRecord(
                device_id=device.id,
                org_id=device.org_id,
                tenant_id=device.tenant_id,
                data_type=DATA_TYPE_AI_BOX_CODE,
                is_related_ledger=False,
                submit_date=submit_date,
                status="ALARM",
                payload=payload,
                detail_json=info,
                source=SOURCE_DEVICE_AUTO,
                process_result=PROCESS_RESULT_SUCCESS
            )
            db.add(record)
            db.commit()
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload for aibox message")
    except Exception as e:
        logger.exception(f"Error processing MQTT message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt_client() -> None:
    try:
        mqtt_client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
        mqtt_client.loop_start()
    except Exception as e:
        logger.exception(f"Error starting MQTT client: {e}")

def stop_mqtt_client() -> None:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

