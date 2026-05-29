// 重新匯出 Wails 產生的 Customer / Worksheet 類別, 加上幾個小幫手函式.
// 讓型別的源頭維持在 bindings, 這樣傳值回 Go 時 service 的簽章可以精確對齊.

import {
  Customer,
  Worksheet,
} from "../../bindings/hgsys/pkg/domain";

export { Customer, Worksheet };

export function emptyCustomer(): Customer {
  return new Customer();
}

export function emptyWorksheet(cid = ""): Worksheet {
  return new Worksheet({ cid });
}

export function phoneList(c: Customer): [string, string, string, string] {
  const parts = c.phones ? c.phones.split(";") : [];
  return [parts[0] ?? "", parts[1] ?? "", parts[2] ?? "", parts[3] ?? ""];
}
