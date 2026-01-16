# IAP: /subscription/update 導入メモ（MVP）

このドキュメントは、スマホアプリ（iOS/Android）のアプリ内課金（IAP）購入完了を受けて、
MashOS（FastAPI）側で `profiles.subscription_tier` を更新するための最小構成メモです。

---

## エンドポイント

- **POST** `/subscription/update`
- **GET** `/subscription/me`（クライアントの表示/ゲート用）

### 認証

`Authorization: Bearer <supabase_access_token>`

- Supabase Auth のアクセストークンを受け取り、`/auth/v1/user` で user_id を解決します。

---

## リクエスト（JSON）

主にアプリ側（react-native-iap）から送られます。

- `platform`：`ios` / `android`
- `product_id`：IAPのSKU（例：`cocolon_plus_monthly`）
- `purchase_token`：AndroidのpurchaseToken（あれば）
- `transaction_receipt`：iOSのbase64 receipt（または transactionReceipt）
- `transaction_id`：iOS transactionId（任意・ログ用）
- `subscription_tier`：`plus` / `premium`（任意・基本は product_id から導出）

> MVPでは `purchase_token` か `transaction_receipt` のどちらかが必須です。

---

## レスポンス（JSON）

- `subscription_tier`：更新後tier
- `allowed_myprofile_modes`：tierに応じた許可モード（`light/standard/deep`）
- `verification`：検証モード（MVPでは `unverified_dev` 等）

---

## Supabase 側の前提

`public.profiles` に `subscription_tier` カラムが必要です。

```sql
alter table public.profiles
  add column if not exists subscription_tier text not null default 'free';

alter table public.profiles
  add constraint profiles_subscription_tier_check
  check (subscription_tier in ('free','plus','premium'));
```

---

## 必須環境変数（サーバー）

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

---

## product_id → tier のマッピング（推奨）

SKUを複数持つ（月額/年額など）場合に備えて、カンマ区切りで指定できます。

### iOS
- `COCOLON_IAP_IOS_PLUS_PRODUCT_IDS`
- `COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS`

### Android
- `COCOLON_IAP_ANDROID_PLUS_PRODUCT_IDS`
- `COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_IDS`

例：

```bash
COCOLON_IAP_IOS_PLUS_PRODUCT_IDS=cocolon_plus_monthly,cocolon_plus_yearly
COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS=cocolon_premium_monthly
```

---

## 検証（Verification）について（重要）

本番では Apple/Google のサーバー検証を必ず入れてください。

MVP（開発/検証）用に、未検証更新を許可するスイッチがあります。

### 1) 全体を未検証許可（危険：devのみ）

```bash
COCOLON_IAP_ALLOW_UNVERIFIED=true
```

### 2) ユーザー限定の未検証許可（推奨：dev/staging）

```bash
COCOLON_IAP_ALLOW_UNVERIFIED_USER_IDS=<supabase_user_id_1>,<supabase_user_id_2>
```

---

## 動作確認（curl例）

```bash
curl -X POST "https://mashos-api.onrender.com/subscription/update" \
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "ios",
    "product_id": "cocolon_plus_monthly",
    "transaction_receipt": "BASE64...",
    "subscription_tier": "plus"
  }'
```

