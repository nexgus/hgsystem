// Re-exports the Wails-generated Customer / Worksheet classes plus tiny
// helpers. Keeping the type origin in the bindings means service signatures
// match exactly when sending values back to Go.

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
