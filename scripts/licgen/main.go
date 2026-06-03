// Command licgen 讀取 module 清單 (path\tdir\tversion) 與直接依賴清單, 偵測每
// 個 module 的授權種類並擷取授權全文 (含 NOTICE), 依是否為直接依賴分別輸出
// frontend/src/licenses-go.ts 的 GO_DIRECT_LICENSES 與 GO_TRANSITIVE_LICENSES
// 兩個陣列. 由 scripts/gen-licenses.sh 呼叫.
//
// 用法:
//
//	go run . <modules.tsv> <direct.txt>
//
// modules.tsv 每行為 "<module path>\t<module dir>\t<version>"; dir 為該
// module 於本機 module cache 的目錄, 供讀取 LICENSE / NOTICE 檔.
// direct.txt 每行一個「直接依賴」的 module path (取自 hgsys/go.mod 之 require
// 中非 indirect 者); 出現於其中者歸入 GO_DIRECT_LICENSES, 其餘歸間接.
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"github.com/google/licensecheck"
)

type entry struct {
	name   string
	url    string
	typ    string
	text   string
	direct bool
}

// licenseNameRe 比對常見授權檔名 (LICENSE / LICENCE / COPYING / COPYRIGHT).
var licenseNameRe = regexp.MustCompile(`(?i)^(LICEN[SC]E|COPYING|COPYRIGHT)([.\-].*)?$`)

// noticeNameRe 比對 NOTICE 檔名 (Apache-2.0 等要求隨附).
var noticeNameRe = regexp.MustCompile(`(?i)^NOTICE([.\-].*)?$`)

// pickLicenseFile 於 module 目錄頂層挑選最適合的授權檔; 純 "LICENSE" 優先,
// 其次依字典序. 回傳絕對路徑, 找不到時回傳空字串.
func pickLicenseFile(dir string) string {
	ents, err := os.ReadDir(dir)
	if err != nil {
		return ""
	}
	var cands []string
	for _, e := range ents {
		if !e.IsDir() && licenseNameRe.MatchString(e.Name()) {
			cands = append(cands, e.Name())
		}
	}
	if len(cands) == 0 {
		return ""
	}
	sort.Slice(cands, func(i, j int) bool {
		bi := strings.ToUpper(strings.SplitN(cands[i], ".", 2)[0])
		bj := strings.ToUpper(strings.SplitN(cands[j], ".", 2)[0])
		if (bi == "LICENSE") != (bj == "LICENSE") {
			return bi == "LICENSE"
		}
		return cands[i] < cands[j]
	})
	return filepath.Join(dir, cands[0])
}

// findNotice 回傳 module 目錄頂層的 NOTICE 檔絕對路徑 (無則空字串).
func findNotice(dir string) string {
	ents, err := os.ReadDir(dir)
	if err != nil {
		return ""
	}
	for _, e := range ents {
		if !e.IsDir() && noticeNameRe.MatchString(e.Name()) {
			return filepath.Join(dir, e.Name())
		}
	}
	return ""
}

// classify 回傳涵蓋率 (以比對字元跨度估計) 最高的單一授權 ID, 避免同檔觸發
// 多個相近樣式 (如 BSD-2-Clause 與 ISC) 時誤標為多重授權.
func classify(text []byte) string {
	cov := licensecheck.Scan(text)
	span := map[string]int{}
	for _, m := range cov.Match {
		span[m.ID] += m.End - m.Start
	}
	best, bestSpan := "", -1
	for id, s := range span {
		if s > bestSpan {
			best, bestSpan = id, s
		}
	}
	return best
}

// jsonStr 將字串編成 JS 字串字面量 (正確跳脫換行 / 引號等, 不跳脫 HTML 字元).
func jsonStr(s string) string {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(s)
	return strings.TrimRight(buf.String(), "\n")
}

// readLines 讀取檔案內以換行分隔的非空 token, 回傳集合.
func readLines(path string) map[string]bool {
	set := map[string]bool{}
	data, err := os.ReadFile(path)
	if err != nil {
		panic(err)
	}
	for _, l := range strings.Split(strings.TrimRight(string(data), "\n"), "\n") {
		if l = strings.TrimSpace(l); l != "" {
			set[l] = true
		}
	}
	return set
}

// emit 將一組 entry 輸出為具名的 ThirdPartyLicense 陣列.
func emit(b *strings.Builder, name string, es []entry) {
	b.WriteString("export const " + name + ": ThirdPartyLicense[] = [\n")
	for _, e := range es {
		b.WriteString("  {\n")
		b.WriteString("    name: " + jsonStr(e.name) + ",\n")
		b.WriteString("    url: " + jsonStr(e.url) + ",\n")
		b.WriteString("    type: " + jsonStr(e.typ) + ",\n")
		b.WriteString("    text: " + jsonStr(e.text) + ",\n")
		b.WriteString("  },\n")
	}
	b.WriteString("];\n")
}

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintln(os.Stderr, "用法: go run . <modules.tsv> <direct.txt>")
		os.Exit(2)
	}
	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		panic(err)
	}
	direct := readLines(os.Args[2])

	var entries []entry
	for _, line := range strings.Split(strings.TrimRight(string(data), "\n"), "\n") {
		if line == "" {
			continue
		}
		cols := strings.Split(line, "\t")
		path, dir := cols[0], cols[1]
		abs := pickLicenseFile(dir)
		if abs == "" {
			fmt.Fprintf(os.Stderr, "WARN: no license file for %s\n", path)
			continue
		}
		body, err := os.ReadFile(abs)
		if err != nil {
			fmt.Fprintf(os.Stderr, "WARN: read %s: %v\n", path, err)
			continue
		}
		typ := classify(body)
		if typ == "" {
			fmt.Fprintf(os.Stderr, "WARN: unrecognised license for %s\n", path)
		}
		text := string(body)
		if np := findNotice(dir); np != "" {
			if nb, err := os.ReadFile(np); err == nil && len(strings.TrimSpace(string(nb))) > 0 {
				text = strings.TrimRight(text, "\n") + "\n\n--- NOTICE ---\n\n" + string(nb)
			}
		}
		entries = append(entries, entry{
			name:   path,
			url:    "https://pkg.go.dev/" + path,
			typ:    typ,
			text:   strings.TrimRight(text, "\n"),
			direct: direct[path],
		})
	}

	// 依是否為直接依賴拆成兩組, 各自依 module 路徑 (不分大小寫) 排序.
	var dir, trans []entry
	for _, e := range entries {
		if e.direct {
			dir = append(dir, e)
		} else {
			trans = append(trans, e)
		}
	}
	byName := func(es []entry) {
		sort.Slice(es, func(i, j int) bool {
			return strings.ToLower(es[i].name) < strings.ToLower(es[j].name)
		})
	}
	byName(dir)
	byName(trans)

	var b strings.Builder
	b.WriteString(`// 本檔為自動產生, 請勿手動編輯. 重新產生: bash scripts/gen-licenses.sh
//
// 內容為 hgsystem 散布物 (hgsystem 執行檔, 及其內嵌的 hgupgrade 自我更新
// 輔助程式) 於 darwin 與 windows 平台實際編譯進 binary 的 Go 依賴及其授權,
// 依 hgsys/go.mod 分為直接 (GO_DIRECT_LICENSES) 與間接 (GO_TRANSITIVE_LICENSES)
// 兩類. 前端依賴 (Vue / @wailsio/runtime) 與應用圖示非 Go module, 列於
// licenses.ts.
//
// 產生方式: 以 go list -deps 取得 darwin + windows 兩平台的相依 module 聯集,
// 以 go.mod 的 require (非 indirect) 判定直接依賴, 再以 google/licensecheck
// 偵測各 module LICENSE 檔的授權種類; 授權全文逐字取自各 module 的 LICENSE
// (Apache-2.0 等若附 NOTICE 一併納入).

import type { ThirdPartyLicense } from "./licenses";

// GO_DIRECT_LICENSES 為 hgsystem 直接依賴的 Go module, 依路徑 (不分大小寫) 排序.
`)
	emit(&b, "GO_DIRECT_LICENSES", dir)
	b.WriteString("\n// GO_TRANSITIVE_LICENSES 為間接 (transitive) 依賴, 依路徑 (不分大小寫) 排序.\n")
	emit(&b, "GO_TRANSITIVE_LICENSES", trans)
	fmt.Print(b.String())
}
