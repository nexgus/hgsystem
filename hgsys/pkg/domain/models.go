// Package domain 內含 hgsystem 應用程式之純資料型別. 此處不含 Mongo 或 UI 相依,
// 以便可獨立進行 unit test.
package domain

import (
	"strings"
	"time"
)

// Customer 對應舊版 `customers` collection 的文件結構.
//
// Phones 為以 ";" 分隔的原始字串 (最多 4 組號碼), 原樣保留以與歷史 Mongo dump
// 相容.
type Customer struct {
	ID        string     `bson:"_id,omitempty"   json:"id"`
	Name      string     `bson:"name"            json:"name"`
	Title     string     `bson:"title"           json:"title"`
	Birthdate *time.Time `bson:"birthdate"       json:"birthdate"`
	Phones    string     `bson:"phones"          json:"phones"`
	Addr      string     `bson:"addr"            json:"addr"`
	Broker    string     `bson:"broker"          json:"broker"`
}

// PhoneList 將 Phones 拆為恰好 4 個欄位, 不足者以空字串補齊.
func (c Customer) PhoneList() [4]string {
	var out [4]string
	if c.Phones == "" {
		return out
	}
	parts := strings.Split(c.Phones, ";")
	for i := 0; i < 4 && i < len(parts); i++ {
		out[i] = parts[i]
	}
	return out
}

// Worksheet 對應舊版 `worksheets` collection 的文件結構.
//
// CID 為對應 Customer.ID 的外鍵. 處方相關欄位沿用舊有字串表示 (來自驗光單上的
// 自由格式文字).
type Worksheet struct {
	ID          string     `bson:"_id,omitempty"  json:"id"`
	CID         string     `bson:"cid"            json:"cid"`
	OrderTime   *time.Time `bson:"order_time"     json:"orderTime"`
	DeliverTime *time.Time `bson:"deliver_time"   json:"deliverTime"`
	SphR        string     `bson:"sph_r"          json:"sphR"`
	SphL        string     `bson:"sph_l"          json:"sphL"`
	CylR        string     `bson:"cyl_r"          json:"cylR"`
	CylL        string     `bson:"cyl_l"          json:"cylL"`
	AxisR       string     `bson:"axis_r"         json:"axisR"`
	AxisL       string     `bson:"axis_l"         json:"axisL"`
	BaseR       string     `bson:"base_r"         json:"baseR"`
	BaseL       string     `bson:"base_l"         json:"baseL"`
	BCR         string     `bson:"bc_r"           json:"bcR"`
	BCL         string     `bson:"bc_l"           json:"bcL"`
	BCVR        string     `bson:"bcv_r"          json:"bcvR"`
	BCVL        string     `bson:"bcv_l"          json:"bcvL"`
	BCHR        string     `bson:"bch_r"          json:"bchR"`
	BCHL        string     `bson:"bch_l"          json:"bchL"`
	AddR        string     `bson:"add_r"          json:"addR"`
	AddL        string     `bson:"add_l"          json:"addL"`
	PD          string     `bson:"pd"             json:"pd"`
	Source      string     `bson:"source"         json:"source"`
	EyesightR   string     `bson:"eyesight_r"     json:"eyesightR"`
	EyesightL   string     `bson:"eyesight_l"     json:"eyesightL"`
	LensR       string     `bson:"lens_r"         json:"lensR"`
	LensL       string     `bson:"lens_l"         json:"lensL"`
	Frame       string     `bson:"frame"          json:"frame"`
	Memo        string     `bson:"memo"           json:"memo"`
	LensPrice   int        `bson:"lens_price"     json:"lensPrice"`
	FramePrice  int        `bson:"frame_price"    json:"framePrice"`
}
