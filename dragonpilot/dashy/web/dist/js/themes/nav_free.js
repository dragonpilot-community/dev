/*
 * Copyright (c) 2025, Rick Lan
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, and/or sublicense,
 * for non-commercial purposes only, subject to the following conditions:
 *
 * - The above copyright notice and this permission notice shall be included in
 *   all copies or substantial portions of the Software.
 * - Commercial use (e.g. use in a product, service, or activity intended to
 *   generate revenue) is prohibited without explicit written permission from
 *   the copyright holder.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
var v=Object.defineProperty;var w=(t,i,e)=>i in t?v(t,i,{enumerable:!0,configurable:!0,writable:!0,value:e}):t[i]=e;var l=(t,i,e)=>w(t,typeof i!="symbol"?i+"":i,e);var u=(t,i,e)=>new Promise((a,o)=>{var s=d=>{try{r(e.next(d))}catch(c){o(c)}},n=d=>{try{r(e.throw(d))}catch(c){o(c)}},r=d=>d.done?a(d.value):Promise.resolve(d.value).then(s,n);r((e=e.apply(t,i)).next())});(function(){"use strict";class t extends BaseTheme{constructor(){super(),this._mapReady=!1}init(e,a){return u(this,null,function*(){this._canvas=e,this._ctx=a,this._enabled=!0;const o=document.getElementById("videoPlayer");if(o&&(o.style.display="none"),window.NavMap&&NavMap.destroy(),window.NavigationFree&&NavigationFree.init(),window.NavMap){yield NavMap.init();const n=document.getElementById("hud-page-content");n&&(NavMap.show(n,{fullscreen:!0,scale:1.5,interactive:!0,enableRouting:!0,autoTileCache:!0,followResumeDelay:3e3}),this._mapReady=!0)}const s=document.getElementById("hud-page-content");return s&&window.NavSearch&&NavSearch.show(s),!0})}update(e){var s;const a=SmUtils.gps(e),o=SmUtils.speedKmh(e);if(this._mapReady&&window.NavMap&&a.lat!==0&&NavMap.setPosition(a.lat,a.lon,a.heading,o),window.NavSearch&&NavSearch.updatePosition(a.lat,a.lon),(s=window.NavigationFree)!=null&&s.isNavigating()){NavigationFree.updatePosition(a.lat,a.lon,a.heading);const n=NavigationFree.getRoute();n&&window.NavMap&&NavMap.setRoute(n)}}render(e,a,o){if(!this._enabled)return!1;e.clearRect(0,0,a,o);const s=window.sm||{};for(const n of this.constructor.layers){const r=window[n.module];if(r!=null&&r.draw){const d=this._layout.getRect(n.region||"full",a,o);r.draw(e,d,s)}}return!1}destroy(){this._enabled=!1,window.NavMap&&NavMap.destroy(),window.NavigationFree&&NavigationFree.clearRoute(),window.NavSearch&&NavSearch.hide();const e=document.getElementById("videoPlayer");e&&(e.style.display=""),this._mapReady=!1}}l(t,"layout",Layouts.full),l(t,"requiresVideo",!1),l(t,"modules",["NavSidebar","NavHud","NavMap","EdgeIndicators"]),l(t,"layers",[{module:"NavSidebar",region:"full"},{module:"NavHud",region:"full"},{module:"EdgeIndicators",region:"full"}]),window.NavFreeTheme=t})();
