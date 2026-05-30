"""
API 接口测试脚本

测试 Photo-Agent 与后端的所有接口。
"""

import httpx
import json
import sys
from datetime import datetime

# 配置
SERVER_URL = "http://192.168.31.152:8080"
AGENT_TOKEN = "YmF6aGk="
AGENT_ID = "dev-win-001"

headers = {
    "Authorization": f"Bearer {AGENT_TOKEN}",
    "Content-Type": "application/json",
}


def test_heartbeat():
    """测试心跳接口"""
    print("\n" + "=" * 60)
    print("测试 1: POST /api/agent/heartbeat")
    print("=" * 60)
    
    data = {
        "agentId": AGENT_ID,
        "version": "0.1.0",
        "status": "idle",
        "lastScanAt": datetime.now().isoformat(),
        "lastSyncAt": datetime.now().isoformat(),
        "photoCount": 8,
        "gpsPhotoCount": 5,
        "thumbSyncedCount": 0,
        "previewSyncedCount": 0,
        "failedCount": 0,
    }
    
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SERVER_URL}/api/agent/heartbeat",
                json=data,
                headers=headers,
                timeout=10.0,
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("[OK] 心跳接口测试通过")
                    return True
                else:
                    print(f"[FAIL] 心跳接口返回失败: {result.get('error')}")
                    return False
            else:
                print(f"[FAIL] 心跳接口返回错误状态码: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"[FAIL] 心跳接口请求异常: {e}")
        return False


def test_batch_upload_photos():
    """测试批量上传照片索引接口"""
    print("\n" + "=" * 60)
    print("测试 2: POST /api/agent/photos/batch")
    print("=" * 60)
    
    data = {
        "agentId": AGENT_ID,
        "photos": [
            {
                "localPhotoId": "test-photo-001",
                "relativePath": "2025/西藏/IMG_001.jpg",
                "fileName": "IMG_001.jpg",
                "fileSize": 3456789,
                "contentHash": None,
                "mtime": "2025-08-12T10:20:00+00:00",
                "takenAt": "2025-08-12T09:58:00",
                "lat": 28.191379,
                "lng": 86.83015,
                "width": 4032,
                "height": 3024,
                "hasGps": True,
            },
            {
                "localPhotoId": "test-photo-002",
                "relativePath": "2025/西藏/IMG_002.jpg",
                "fileName": "IMG_002.jpg",
                "fileSize": 2345678,
                "contentHash": None,
                "mtime": "2025-08-12T11:30:00+00:00",
                "takenAt": "2025-08-12T11:25:00",
                "lat": 28.192000,
                "lng": 86.83100,
                "width": 4032,
                "height": 3024,
                "hasGps": True,
            },
        ],
    }
    
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SERVER_URL}/api/agent/photos/batch",
                json=data,
                headers=headers,
                timeout=10.0,
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("[OK] 批量上传照片索引接口测试通过")
                    results = result.get("data", {}).get("results", [])
                    print(f"   返回 {len(results)} 条结果")
                    for r in results:
                        print(f"   - {r.get('localPhotoId')} -> {r.get('photoId')}")
                    return True
                else:
                    print(f"[FAIL] 批量上传照片索引接口返回失败: {result.get('error')}")
                    return False
            else:
                print(f"[FAIL] 批量上传照片索引接口返回错误状态码: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"[FAIL] 批量上传照片索引接口请求异常: {e}")
        return False


def test_get_upload_ticket():
    """测试申请 COS 上传地址接口"""
    print("\n" + "=" * 60)
    print("测试 3: POST /api/agent/assets/upload-ticket")
    print("=" * 60)
    
    data = {
        "agentId": AGENT_ID,
        "photoId": "ph001",
        "assetType": "thumb",
        "contentType": "image/webp",
        "fileSize": 52000,
        "width": 360,
        "height": 270,
    }
    
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SERVER_URL}/api/agent/assets/upload-ticket",
                json=data,
                headers=headers,
                timeout=10.0,
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("[OK] 申请 COS 上传地址接口测试通过")
                    upload_data = result.get("data", {})
                    print(f"   storageKey: {upload_data.get('storageKey')}")
                    print(f"   uploadUrl: {upload_data.get('uploadUrl', '')[:50]}...")
                    return True
                else:
                    print(f"[FAIL] 申请 COS 上传地址接口返回失败: {result.get('error')}")
                    return False
            else:
                print(f"[FAIL] 申请 COS 上传地址接口返回错误状态码: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"[FAIL] 申请 COS 上传地址接口请求异常: {e}")
        return False


def test_upload_complete(photo_id="4"):
    """测试通知上传完成接口"""
    print("\n" + "=" * 60)
    print("测试 4: POST /api/agent/assets/upload-complete")
    print("=" * 60)
    
    data = {
        "agentId": AGENT_ID,
        "photoId": photo_id,
        "assetType": "thumb",
        "storageProvider": "cos",
        "storageKey": f"thumbs/{AGENT_ID}/2025/08/{photo_id}.webp",
        "fileSize": 52000,
        "width": 360,
        "height": 270,
    }
    
    print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SERVER_URL}/api/agent/assets/upload-complete",
                json=data,
                headers=headers,
                timeout=10.0,
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("[OK] 通知上传完成接口测试通过")
                    print(f"   assetId: {result.get('data', {}).get('assetId')}")
                    return True
                else:
                    print(f"[FAIL] 通知上传完成接口返回失败: {result.get('error')}")
                    return False
            else:
                print(f"[FAIL] 通知上传完成接口返回错误状态码: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"[FAIL] 通知上传完成接口请求异常: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("Photo-Agent API 接口测试")
    print("=" * 60)
    print(f"服务器地址: {SERVER_URL}")
    print(f"Agent ID: {AGENT_ID}")
    print(f"Agent Token: {AGENT_TOKEN[:10]}...")
    
    results = []
    photo_id = None
    
    # 测试心跳接口
    results.append(("心跳接口", test_heartbeat()))
    
    # 测试批量上传照片索引接口（获取 photoId）
    batch_result = test_batch_upload_photos()
    results.append(("批量上传照片索引", batch_result))
    
    # 如果批量上传成功，获取 photoId 用于后续测试
    if batch_result:
        # 重新调用获取 photoId
        try:
            with httpx.Client() as client:
                data = {
                    "agentId": AGENT_ID,
                    "photos": [
                        {
                            "localPhotoId": "test-photo-001",
                            "relativePath": "2025/西藏/IMG_001.jpg",
                            "fileName": "IMG_001.jpg",
                            "fileSize": 3456789,
                            "contentHash": None,
                            "mtime": "2025-08-12T10:20:00+00:00",
                            "takenAt": "2025-08-12T09:58:00",
                            "lat": 28.191379,
                            "lng": 86.83015,
                            "width": 4032,
                            "height": 3024,
                            "hasGps": True,
                        },
                    ],
                }
                response = client.post(
                    f"{SERVER_URL}/api/agent/photos/batch",
                    json=data,
                    headers=headers,
                    timeout=10.0,
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        results_list = result.get("data", {}).get("results", [])
                        if results_list:
                            photo_id = results_list[0].get("photoId")
                            print(f"\n获取到 photoId: {photo_id}")
        except Exception:
            pass
    
    # 测试申请 COS 上传地址接口
    results.append(("申请 COS 上传地址", test_get_upload_ticket()))
    
    # 测试通知上传完成接口（使用真实的 photoId）
    results.append(("通知上传完成", test_upload_complete(photo_id or "4")))
    
    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有接口测试通过！")
    else:
        print("[WARNING] 部分接口测试失败，请检查后端实现")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
