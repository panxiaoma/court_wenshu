"use strict";

var e = {}
e['navigator'] = {
    "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) " +
        "Chrome/70.0.3538.77 Safari/537.36"
}
e["screen"] = {
    "height": 800,
    "width": 1280
}

function get_um_id(){
    function a() {
        function a(a, b) {
            var c, d = 0;
            for (c = 0; c < b.length; c++) d |= g[c] << 8 * c;
            return a ^ d
        }
        var b = e.navigator.userAgent,
            f, g = [],
            h = 0;
        for (f = 0; f < b.length; f++) {
            var k = b.charCodeAt(f);
            g.unshift(k & 255);
            4 <= g.length && (h = a(h, g), g = [])
        }
        0 < g.length && (h = a(h, g));
        return h.toString(16)
    }
    function b() {
        for (var a = 1 * new Date, b = 0; a == 1 * new Date;) b++;
        return a.toString(16) + b.toString(16)
    }
    var c = (e.screen.height * e.screen.width).toString(16);
    var data =  b() + "-" + Math.random().toString(16).replace(".", "") + "-" + a() + "-" + c + "-" + b()
    return data
}

function cnzz_data(D) {
    // var version = '1261033118'
    // var a = "CNZZDATA" + version + "="
    var b = []
    var d = Math.floor(2147483648 * Math.random()) + "-" + D + "-" + "http://www.gsxt.gov.cn/"
    b.push(encodeURIComponent(d))
    b.push(D)
    return encodeURIComponent(b.join("|"))
}


