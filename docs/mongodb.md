# MongoDB 資料結構與開發環境

本文件說明 hgsystem 的 MongoDB 資料結構, GUI 輸入欄位與資料庫欄位的對應關係, 以及開發環境下以 Docker 啟動 MongoDB, 還原資料庫與目錄對應的方式.

## 1. 概觀

資料庫名稱固定為 `hgsystem` (內嵌於 mongodump 備份中, 不可變動), 共四個 collection.

| Collection | 用途 | 對應 GUI |
| --- | --- | --- |
| `customers` | 客戶基本資料 | 左側「客戶資料」面板 |
| `worksheets` | 配鏡 / 處方單, 以 `cid` 連到客戶 | 右側「配鏡資料」面板 |
| `titles` | 稱謂下拉清單, 每筆文件形如 `{_id: "<稱謂>"}` | 稱謂選單的「新增 / 管理稱謂」 |
| `search` | 本次啟動內檢視過的客戶歷史 (啟動時清空, 非使用者直接輸入) | 搜尋對話框的「歷史」 |

文件 `_id` 為「字串化的 ObjectId」, 並非原生 BSON ObjectId, 此為與既有資料相容的不變式.

## 2. GUI 輸入到資料庫欄位的對應

### 2.1 客戶面板 → `customers`

型別定義於 `hgsys/pkg/domain/models.go`, 表單於 `frontend/src/components/CustomerPanel.vue`.

| GUI 欄位 | BSON 欄位 | 型別 | 備註 |
| --- | --- | --- | --- |
| 姓名 | `name` | string | |
| 稱謂 (下拉) | `title` | string | 空字串代表「無稱謂」; 清單來自 `titles` collection |
| 地址 | `addr` | string | |
| 電話 (四格) | `phones` | string | 四格共同存成同一個字串, 以 `;` 分隔; 為相容歷史 mongodump |
| 生日 | `birthdate` | date (可空) | 採民國年輸入; `9996` 為「年份未知」哨兵 |
| 介紹人 | `broker` | string | |
| 自動產生 | `_id` | string | 字串化 ObjectId |

### 2.2 配鏡面板 → `worksheets`

型別定義於 `hgsys/pkg/domain/models.go`, 表單於 `frontend/src/components/WorksheetPanel.vue`.

外鍵 `cid` 等於所屬客戶的 `_id`. GUI 沒有獨立輸入框, 由目前選取的客戶決定.

日期欄位:

| GUI | BSON | 型別 |
| --- | --- | --- |
| 收件日 | `order_time` | date (可空) |
| 交件日 | `deliver_time` | date (可空) |

處方箋 (左右眼, R = OD, L = OS):

| GUI 列 | 右眼 BSON | 左眼 BSON |
| --- | --- | --- |
| SPH | `sph_r` | `sph_l` |
| CYL | `cyl_r` | `cyl_l` |
| AXIS | `axis_r` | `axis_l` |
| BASE | `base_r` | `base_l` |
| BC | `bc_r` | `bc_l` |
| BC.V | `bcv_r` | `bcv_l` |
| BC.H | `bch_r` | `bch_l` |
| ADD | `add_r` | `add_l` |
| PD | `pd` (單一) | |
| 來源 | `source` (單一) | |

眼鏡資料:

| GUI | 右眼 / 單一 BSON | 左眼 BSON |
| --- | --- | --- |
| 視力 | `eyesight_r` | `eyesight_l` |
| 鏡片 | `lens_r` | `lens_l` |
| 鏡架 | `frame` (單一) | |
| 備註 | `memo` (單一) | |

金額:

| GUI | BSON | 型別 | 備註 |
| --- | --- | --- | --- |
| 鏡片 | `lens_price` | int | |
| 鏡架 | `frame_price` | int | |
| 合計 | 不存 | | 前端即時計算 `lensPrice + framePrice`, 不寫入資料庫 |

### 2.3 稱謂與搜尋歷史

- `titles`: 每筆文件即 `{_id: "<稱謂>"}`, 整個清單就是此 collection 的所有 `_id`. 空字串「無稱謂」不存入. 客戶舊資料中不在清單內的「髒值」title 不會被寫進 `titles`, 而是原樣留在該客戶文件, 並在下拉選單以「(目前) ...」顯示.
- `search`: 僅為本次啟動內檢視過客戶的副本, 依 `_id` 去重, 每次啟動時清空, 不屬於使用者直接輸入的資料.

### 2.4 需留意的點

1. 電話是一個欄位, 不是四個. UI 有四格, 資料庫只有 `phones` 一個以 `;` 分隔的字串, 拆合由 `PhoneList()` 與 `phoneList()` 負責.
2. 合計不入庫. 只儲存 `lens_price` 與 `frame_price` 兩個數字, 合計為顯示用的衍生值.
3. 所有處方與眼鏡欄位皆為自由字串 (沿用驗光單上的原始文字), 並非數值型別.
4. Go 的 bson tag 與前端 json key 命名不同 (例如 `sph_r` 對應 `sphR`), 由 Wails bindings 自動橋接, 前端 `Worksheet` 使用 camelCase.

## 3. 開發環境的 MongoDB (Docker)

執行期 (非編譯期) 需要可連線的 MongoDB. 開發環境以 Docker 容器 `hgsys-mongo` 提供, 映像為 `mongo:latest`, 無帳號密碼, 對應到本機 `127.0.0.1:27017`. 應用程式預設連線 `localhost:27017`, 可由 `-H` / `-p` 旗標調整.

### 3.1 啟動容器

於專案根目錄執行:

```sh
docker run -d --name hgsys-mongo \
  -p 127.0.0.1:27017:27017 \
  -v "$(pwd)/data:/data/db" \
  -v "$(pwd)/db_backup:/backup:ro" \
  mongo:latest
```

### 3.2 資料庫對應到本機目錄

容器掛載兩個 bind mount:

| 本機目錄 | 容器內路徑 | 模式 | 用途 |
| --- | --- | --- | --- |
| `./data` | `/data/db` | 讀寫 | MongoDB 實際資料落地處. 刪除 `./data` 等於清空整個資料庫 |
| `./db_backup` | `/backup` | 唯讀 | 放置 mongodump 備份, 供容器內還原使用 |

`./data` 與 `./db_backup` 皆已列入 `.gitignore` (屬私有資料), 不進版控.

### 3.3 還原資料庫

`db_backup/` 內為 mongodump 的 BSON 格式: `customers`, `worksheets`, `search` 各一組 `.bson` 與 `.metadata.json`. 不含 `titles`, 因為稱謂清單於應用程式首次啟動時由 `SeedIfEmpty` 自動建立預設值.

從容器內還原 (備份已掛載於 `/backup`):

```sh
docker exec hgsys-mongo mongorestore --drop --db hgsystem /backup
```

或從本機還原 (需本機 PATH 上有 `mongorestore`):

```sh
mongorestore --host 127.0.0.1 --port 27017 --drop --db hgsystem ./db_backup
```

`--drop` 會在還原前清掉同名 collection 的既有資料; 若要保留現有資料則移除此旗標.

### 3.4 常用維運指令

```sh
docker start hgsys-mongo            # 啟動既有容器
docker stop hgsys-mongo             # 停止容器
docker logs -f hgsys-mongo          # 觀察日誌
docker exec -it hgsys-mongo mongosh # 進入 mongosh 互動查詢

# 在 mongosh 內檢視資料
use hgsystem
db.customers.findOne()
db.worksheets.countDocuments()
```

備份與還原功能在應用程式內亦有對應 (主畫面「資料」選單的備份 / 還原), 同樣以 `mongodump` / `mongorestore` 子程序執行, 因此這兩個工具需位於 PATH 上.
