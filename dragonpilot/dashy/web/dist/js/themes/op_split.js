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
var c=Object.defineProperty;var _=(s,r,t)=>r in s?c(s,r,{enumerable:!0,configurable:!0,writable:!0,value:t}):s[r]=t;var l=(s,r,t)=>_(s,typeof r!="symbol"?r+"":r,t);var p=(s,r,t)=>new Promise((e,n)=>{var d=a=>{try{i(t.next(a))}catch(h){n(h)}},o=a=>{try{i(t.throw(a))}catch(h){n(h)}},i=a=>a.done?e(a.value):Promise.resolve(a.value).then(d,o);i((t=t.apply(s,r)).next())});(function(){"use strict";class s extends BaseTheme{constructor(){super(),this._splitContainer=null,this._mapContainer=null,this._videoContainer=null,this._videoCanvas=null,this._videoCtx=null,this._opModel=null,this._minimapReady=!1,this._isPortrait=!1,this._resizeHandler=null}init(t,e){return p(this,null,function*(){return this._canvas=t,this._ctx=e,this._enabled=!0,window.Minimap&&Minimap.destroy(),window.NavMap&&NavMap.destroy(),this._createSplitLayout(),yield this._initMap(),this._resizeHandler=()=>this._handleResize(),window.addEventListener("resize",this._resizeHandler),!0})}_handleResize(){const t=window.innerWidth,e=window.innerHeight,n=this._isPortrait;this._isPortrait=this._layout.isPortrait(t,e),n!==this._isPortrait&&this._rebuildLayout()}_rebuildLayout(){const t=this._minimapReady;this._minimapReady&&window.NavMap&&NavMap.destroy(),this._minimapReady=!1;const e=document.getElementById("videoPlayer"),n=document.getElementById("hud-page-content");e&&this._videoContainer&&n&&(e.style.cssText="",n.insertBefore(e,this._videoContainer),this._videoContainer.remove()),this._splitContainer&&this._splitContainer.remove(),this._createSplitLayout(),t&&this._initMap()}_createSplitLayout(){const t=document.getElementById("hud-page-content");if(!t)return;const e=t.offsetWidth||window.innerWidth,n=t.offsetHeight||window.innerHeight;this._isPortrait=this._layout.isPortrait(e,n);const d=this._layout.getRegionRect("primary",e,n),o=this._layout.getRegionRect("secondary",e,n),i=60;this._splitContainer=document.createElement("div"),this._splitContainer.id="op-split-container",this._splitContainer.style.cssText=`
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            display: flex; pointer-events: none; z-index: 1;
            flex-direction: ${this._isPortrait?"column-reverse":"row-reverse"};
        `,this._mapContainer=document.createElement("div"),this._mapContainer.id="op-split-map",this._isPortrait?this._mapContainer.style.cssText=`
                width: ${d.width}px; height: ${d.height}px;
                position: relative; pointer-events: auto;
                -webkit-mask-image: linear-gradient(to top, black 0%, black calc(100% - ${i}px), transparent 100%);
                mask-image: linear-gradient(to top, black 0%, black calc(100% - ${i}px), transparent 100%);
            `:this._mapContainer.style.cssText=`
                width: ${d.width}px; height: ${d.height}px;
                position: relative; pointer-events: auto;
                -webkit-mask-image: linear-gradient(to left, black 0%, black calc(100% - ${i}px), transparent 100%);
                mask-image: linear-gradient(to left, black 0%, black calc(100% - ${i}px), transparent 100%);
            `,this._splitContainer.appendChild(this._mapContainer),t.appendChild(this._splitContainer);const a=document.getElementById("videoPlayer");a&&(this._videoContainer=document.createElement("div"),this._videoContainer.id="op-split-video",this._isPortrait?this._videoContainer.style.cssText=`
                    position: absolute; left: ${o.x}px; top: 0;
                    width: ${o.width}px; height: ${o.height+i}px;
                    overflow: hidden;
                    -webkit-mask-image: linear-gradient(to top, transparent 0%, black ${i}px, black 100%);
                    mask-image: linear-gradient(to top, transparent 0%, black ${i}px, black 100%);
                `:this._videoContainer.style.cssText=`
                    position: absolute; left: 0; top: ${o.y}px;
                    width: ${o.width+i}px; height: ${o.height}px;
                    overflow: hidden;
                    -webkit-mask-image: linear-gradient(to left, transparent 0%, black ${i}px, black 100%);
                    mask-image: linear-gradient(to left, transparent 0%, black ${i}px, black 100%);
                `,a.parentNode.insertBefore(this._videoContainer,a),this._videoContainer.appendChild(a),a.style.cssText=`
                position: absolute; top: 0; left: 0;
                width: 100%; height: 100%;
                object-fit: cover;
            `,this._videoCanvas=document.createElement("canvas"),this._videoCanvas.width=o.width,this._videoCanvas.height=o.height,this._videoCanvas.style.cssText=`
                position: absolute; top: 0; left: 0;
                width: 100%; height: 100%; pointer-events: none;
            `,this._videoContainer.appendChild(this._videoCanvas),this._videoCtx=this._videoCanvas.getContext("2d"),window.OpModel&&(this._opModel=OpModel.create()))}_initMap(){return p(this,null,function*(){!this._mapContainer||!window.NavMap||(NavMap.destroy(),yield NavMap.init(),NavMap.show(this._mapContainer,{fullscreen:!0,scale:1.5,zoom:16,interactive:!0}),this._minimapReady=!0)})}update(t){if(this._minimapReady&&window.NavMap&&NavMap.isVisible()){const e=SmUtils.gps(t);e.lat!==0&&NavMap.setPosition(e.lat,e.lon,e.heading,SmUtils.speedKmh(t))}}render(t,e,n){if(!this._enabled)return!1;const d=window.sm||{};this._opModel&&this._videoCtx&&(this._videoCtx.clearRect(0,0,this._videoCanvas.width,this._videoCanvas.height),this._opModel.draw(this._videoCtx,{x:0,y:0,width:this._videoCanvas.width,height:this._videoCanvas.height},d));for(const o of this.constructor.layers){const i=window[o.module];if(!(i!=null&&i.draw))continue;let a;o.region==="hud"?this._isPortrait?a={x:0,y:0,width:e,height:n*.5}:a={x:0,y:0,width:e*.5,height:n}:a={x:0,y:0,width:e,height:n},i.draw(t,a,d)}return!1}destroy(){this._enabled=!1,this._resizeHandler&&(window.removeEventListener("resize",this._resizeHandler),this._resizeHandler=null),this._minimapReady&&window.NavMap&&NavMap.destroy(),this._opModel&&this._opModel.destroy();const t=document.getElementById("videoPlayer"),e=document.getElementById("hud-page-content");t&&this._videoContainer&&e&&(t.style.cssText="",t.className="absolute inset-0 w-full h-full object-cover",e.insertBefore(t,this._videoContainer),this._videoContainer.remove()),this._splitContainer&&this._splitContainer.remove(),this._splitContainer=null,this._mapContainer=null,this._videoContainer=null,this._videoCanvas=null,this._videoCtx=null,this._opModel=null,this._minimapReady=!1,this._isPortrait=!1}}l(s,"layout",Layouts.splitResponsive),l(s,"requiresVideo",!0),l(s,"handlesOwnRendering",!0),l(s,"modules",["NavSidebar","NavMap","OpModel","OpBorder","OpAlerts","EdgeIndicators"]),l(s,"layers",[{module:"NavSidebar",region:"hud"},{module:"OpBorder",region:"full"},{module:"EdgeIndicators",region:"full"},{module:"OpAlerts",region:"full"}]),window.OpSplitTheme=s})();
