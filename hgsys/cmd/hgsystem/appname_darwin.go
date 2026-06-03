package main

/*
#cgo CFLAGS: -x objective-c
#cgo LDFLAGS: -framework Foundation
#include <stdlib.h>
#import <Foundation/Foundation.h>

// setAppName 設定 macOS 應用程式選單顯示的應用名稱.
//
// 未打包成 .app bundle 的執行檔, 應用程式選單 (main menu 第一項) 的粗體標題
// 取自主 bundle 的 CFBundleName; 缺少 Info.plist 時該值為空, AppKit 退回以裸
// 執行檔的檔名顯示. 主 bundle 的 infoDictionary 於執行期為可變字典, 在
// NSApplication 初始化前注入 CFBundleName, 即可讓該標題改顯示自訂名稱;
// 一併覆寫 NSProcessInfo 的 processName 以維持一致. 以 @try / @catch 包覆,
// 任一步驟失敗時靜默維持預設, 不影響其他功能.
static void setAppName(const char *name) {
    @try {
        NSString *s = [NSString stringWithUTF8String:name];
        NSMutableDictionary *info = (NSMutableDictionary *)[[NSBundle mainBundle] infoDictionary];
        [info setObject:s forKey:@"CFBundleName"];
        [[NSProcessInfo processInfo] setValue:s forKey:@"processName"];
    } @catch (NSException *e) {
        // 維持預設名稱, 不影響其他功能.
    }
}
*/
import "C"

import "unsafe"

// setAppName 設定 macOS 應用程式選單顯示的應用名稱, 使其顯示自訂名稱而非裸
// 執行檔的檔名. 須於建立 application 前呼叫; 僅 darwin 有實際作用.
func setAppName(name string) {
	c := C.CString(name)
	defer C.free(unsafe.Pointer(c))
	C.setAppName(c)
}
