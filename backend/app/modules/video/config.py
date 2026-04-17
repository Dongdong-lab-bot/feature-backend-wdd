from app.core.config import settings

def build_stream_key(tenant_id: int, camera_id: int) -> str:
    """
    构建流媒体 Stream Key
    格式：t_{tenant_id}_c_{camera_id}
    
    Args:
        tenant_id: 租户ID
        camera_id: 摄像头ID
    
    Returns:
        Stream Key
    """
    return f"t_{tenant_id}_c_{camera_id}"

def build_hls_url(stream_key: str) -> str:
    """
    构建 HLS 播放地址
    
    Args:
        stream_key: Stream Key
    
    Returns:
        HLS 播放地址
    """
    return f"http://{settings.media_server_host}:{settings.media_server_hls_port}/{stream_key}/index.m3u8"

def build_webrtc_url(stream_key: str) -> str:
    """
    构建 WebRTC 播放地址
    
    Args:
        stream_key: Stream Key
    
    Returns:
        WebRTC 播放地址
    """
    return f"http://{settings.media_server_host}:{settings.media_server_webrtc_port}/{stream_key}"