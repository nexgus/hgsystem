import { createApp } from "vue";
import App from "./App.vue";
import About from "./About.vue";
import "./style.css";

// 依 URL hash 決定掛載的畫面: #about / #about-license 為「關於」視窗, 其餘為
// 主視窗. 「關於」視窗由 Go 端選單以獨立 window 開啟並帶入該 hash.
const isAbout = location.hash.startsWith("#about");

createApp(isAbout ? About : App).mount("#app");
