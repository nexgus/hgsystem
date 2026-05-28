// Package domain holds pure data types for the hgsystem app. No Mongo or UI
// dependencies live here so it can be unit-tested in isolation.
package domain

import (
	"strings"
	"time"
)

// Customer mirrors the legacy `customers` collection document.
//
// Phones is the ";"-separated raw string (up to 4 numbers) kept verbatim to
// stay compatible with historical Mongo dumps.
type Customer struct {
	ID        string     `bson:"_id,omitempty"   json:"id"`
	Name      string     `bson:"name"            json:"name"`
	Title     string     `bson:"title"           json:"title"`
	Birthdate *time.Time `bson:"birthdate"       json:"birthdate"`
	Phones    string     `bson:"phones"          json:"phones"`
	Addr      string     `bson:"addr"            json:"addr"`
	Broker    string     `bson:"broker"          json:"broker"`
}

// PhoneList splits Phones into exactly 4 slots, padding with empty strings.
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

// Worksheet mirrors the legacy `worksheets` collection document.
//
// CID is the foreign key to Customer.ID. Prescription columns keep their
// historical string representation (free-form text from the eye-care form).
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
