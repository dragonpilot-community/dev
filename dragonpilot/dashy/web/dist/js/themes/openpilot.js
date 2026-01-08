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
var n=Object.defineProperty;var u=(r,e,d)=>e in r?n(r,e,{enumerable:!0,configurable:!0,writable:!0,value:d}):r[e]=d;var s=(r,e,d)=>u(r,typeof e!="symbol"?e+"":e,d);(function(){"use strict";class r extends HudRenderer{render(t,i,a){return super.render(t,i,a),window.EdgeIndicators&&EdgeIndicators.draw(a,t,i),!1}}window.OpenpilotHudRenderer=r;class e extends BaseTheme{}s(e,"layout",Layouts.fullResponsive),s(e,"requiresVideo",!0),s(e,"modules",["OpHud","OpBorder","OpAlerts","NavMap","EdgeIndicators"]),s(e,"layers",[]),s(e,"minimapConfig",{useGrid:!1,options:{responsiveThird:!0,zoom:16,interactive:!0,scale:1.5}}),s(e,"hudRenderer","OpenpilotHudRenderer"),window.OpenpilotTheme=e})();
