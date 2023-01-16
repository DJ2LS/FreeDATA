/*
 * Copyright (c) 2019 Jeppe Ledet-Pedersen
 * This software is released under the MIT license.
 * See the LICENSE file for further details.
 */

'use strict';

Spectrum.prototype.squeeze = function(value, out_min, out_max) {
    if (value <= this.min_db)
        return out_min;
    else if (value >= this.max_db)
        return out_max;
    else
        return Math.round((value - this.min_db) / (this.max_db - this.min_db) * out_max);
}

Spectrum.prototype.rowToImageData = function(bins) {
    for (var i = 0; i < this.imagedata.data.length; i += 4) {
        var cindex = this.squeeze(bins[i/4], 0, 255);
        var color = this.colormap[cindex];
        this.imagedata.data[i+0] = color[0];
        this.imagedata.data[i+1] = color[1];
        this.imagedata.data[i+2] = color[2];
        this.imagedata.data[i+3] = 255;
    }
}

Spectrum.prototype.addWaterfallRow = function(bins) {
    // Shift waterfall 1 row down
    this.ctx_wf.drawImage(this.ctx_wf.canvas,
        0, 0, this.wf_size, this.wf_rows - 1,
        0, 1, this.wf_size, this.wf_rows - 1);

    // Draw new line on waterfall canvas
    this.rowToImageData(bins);
    this.ctx_wf.putImageData(this.imagedata, 0, 0);

    var width = this.ctx.canvas.width;
    var height = this.ctx.canvas.height;

    // Copy scaled FFT canvas to screen. Only copy the number of rows that will
    // fit in waterfall area to avoid vertical scaling.
    this.ctx.imageSmoothingEnabled = false;
    var rows = Math.min(this.wf_rows, height - this.spectrumHeight);
    this.ctx.drawImage(this.ctx_wf.canvas,
        0, 0, this.wf_size, rows,
        0, this.spectrumHeight, width, height - this.spectrumHeight);
}

Spectrum.prototype.drawFFT = function(bins) {
    this.ctx.beginPath();
    this.ctx.moveTo(-1, this.spectrumHeight + 1);
    for (var i = 0; i < bins.length; i++) {
        var y = this.spectrumHeight - this.squeeze(bins[i], 0, this.spectrumHeight);
        if (y > this.spectrumHeight - 1)
            y = this.spectrumHeight + 1; // Hide underflow
        if (y < 0)
            y = 0;
        if (i == 0)
            this.ctx.lineTo(-1, y);
        this.ctx.lineTo(i, y);
        if (i == bins.length - 1)
            this.ctx.lineTo(this.wf_size + 1, y);
    }
    this.ctx.lineTo(this.wf_size + 1, this.spectrumHeight + 1);
    this.ctx.strokeStyle = "#fefefe";
    this.ctx.stroke();
}

//Spectrum.prototype.drawSpectrum = function(bins) {
    Spectrum.prototype.drawSpectrum = function() {
    var width = this.ctx.canvas.width;
    var height = this.ctx.canvas.height;


    // Modification by DJ2LS
    // Draw bandwidth lines
    // TODO: Math not correct. But a first attempt
    // it seems position is more or less equal to frequenzy by factor 10
    // eg. position 150 == 1500Hz
    /*
    // CENTER LINE
    this.ctx_wf.beginPath();
    this.ctx_wf.moveTo(150,0);
    this.ctx_wf.lineTo(150, height);
    this.ctx_wf.lineWidth = 1;
    this.ctx_wf.strokeStyle = '#8C8C8C';
    this.ctx_wf.stroke()
    */

    // 586Hz and 1700Hz LINES
    var linePositionLow = 121.6;     //150 - bandwith/20
    var linePositionHigh = 178.4;    //150 + bandwidth/20
    var linePositionLow2 = 65;       //150 - bandwith/20
    var linePositionHigh2 = 235;     //150 + bandwith/20  
    this.ctx_wf.beginPath();
    this.ctx_wf.moveTo(linePositionLow,0);
    this.ctx_wf.lineTo(linePositionLow, height);
    this.ctx_wf.moveTo(linePositionHigh,0);
    this.ctx_wf.lineTo(linePositionHigh, height);
    this.ctx_wf.moveTo(linePositionLow2,0);
    this.ctx_wf.lineTo(linePositionLow2, height);
    this.ctx_wf.moveTo(linePositionHigh2,0);
    this.ctx_wf.lineTo(linePositionHigh2, height);
    this.ctx_wf.lineWidth = 1;
    this.ctx_wf.strokeStyle = '#C3C3C3';
    this.ctx_wf.stroke()

   // ---- END OF MODIFICATION ------


    // Fill with black
    this.ctx.fillStyle = "white";
    this.ctx.fillRect(0, 0, width, height);

    //Commenting out the remainder of this code, it's not needed and unused as of 6.9.11 and saves three if statements
    return;
    /*
    // FFT averaging
    if (this.averaging > 0) {
        if (!this.binsAverage || this.binsAverage.length != bins.length) {
            this.binsAverage = Array.from(bins);
        } else {
            for (var i = 0; i < bins.length; i++) {
                this.binsAverage[i] += this.alpha * (bins[i] - this.binsAverage[i]);
            }
        }
        bins = this.binsAverage;
    }

    // Max hold
    if (this.maxHold) {
        if (!this.binsMax || this.binsMax.length != bins.length) {
            this.binsMax = Array.from(bins);
        } else {
            for (var i = 0; i < bins.length; i++) {
                if (bins[i] > this.binsMax[i]) {
                    this.binsMax[i] = bins[i];
                } else {
                    // Decay
                    this.binsMax[i] = 1.0025 * this.binsMax[i];
                }
            }
        }
    }

    // Do not draw anything if spectrum is not visible
    if (this.ctx_axes.canvas.height < 1)
        return;

    // Scale for FFT
    this.ctx.save();
    this.ctx.scale(width / this.wf_size, 1);

    // Draw maxhold
    if (this.maxHold)
        this.drawFFT(this.binsMax);

    // Draw FFT bins
    this.drawFFT(bins);

    // Restore scale
    this.ctx.restore();

    // Fill scaled path
    this.ctx.fillStyle = this.gradient;
    this.ctx.fill();

    // Copy axes from offscreen canvas
    this.ctx.drawImage(this.ctx_axes.canvas, 0, 0);
    */
}

//Allow setting colormap
Spectrum.prototype.setColorMap = function(index) {
    this.colormap = colormaps[index];
}

Spectrum.prototype.updateAxes = function() {
    var width = this.ctx_axes.canvas.width;
    var height = this.ctx_axes.canvas.height;

    // Clear axes canvas
    this.ctx_axes.clearRect(0, 0, width, height);

    // Draw axes
    this.ctx_axes.font = "12px sans-serif";
    this.ctx_axes.fillStyle = "white";
    this.ctx_axes.textBaseline = "middle";

    this.ctx_axes.textAlign = "left";
    var step = 10;
    for (var i = this.min_db + 10; i <= this.max_db - 10; i += step) {
        var y = height - this.squeeze(i, 0, height);
        this.ctx_axes.fillText(i, 5, y);

        this.ctx_axes.beginPath();
        this.ctx_axes.moveTo(20, y);
        this.ctx_axes.lineTo(width, y);
        this.ctx_axes.strokeStyle = "rgba(200, 200, 200, 0.10)";
        this.ctx_axes.stroke();
    }

    this.ctx_axes.textBaseline = "bottom";
    for (var i = 0; i < 11; i++) {
        var x = Math.round(width / 10) * i;

        if (this.spanHz > 0) {
            var adjust = 0;
            if (i == 0) {
                this.ctx_axes.textAlign = "left";
                adjust = 3;
            } else if (i == 10) {
                this.ctx_axes.textAlign = "right";
                adjust = -3;
            } else {
                this.ctx_axes.textAlign = "center";
            }

            var freq = this.centerHz + this.spanHz / 10 * (i - 5);
            if (this.centerHz + this.spanHz > 1e6)
                freq = freq / 1e6 + "M";
            else if (this.centerHz + this.spanHz > 1e3)
                freq = freq / 1e3 + "k";
            this.ctx_axes.fillText(freq, x + adjust, height - 3);
        }

        this.ctx_axes.beginPath();
        this.ctx_axes.moveTo(x, 0);
        this.ctx_axes.lineTo(x, height);
        this.ctx_axes.strokeStyle = "rgba(200, 200, 200, 0.10)";
        this.ctx_axes.stroke();
    }
}

Spectrum.prototype.addData = function(data) {
    if (!this.paused) {
        if (data.length != this.wf_size) {
            this.wf_size = data.length;
            this.ctx_wf.canvas.width = data.length;
            this.ctx_wf.fillStyle = "white";
            this.ctx_wf.fillRect(0, 0, this.wf.width, this.wf.height);
            this.imagedata = this.ctx_wf.createImageData(data.length, 1);
        }
        //this.drawSpectrum(data);
        this.drawSpectrum();
        this.addWaterfallRow(data);
        this.resize();
    }
}

Spectrum.prototype.updateSpectrumRatio = function() {
    this.spectrumHeight = Math.round(this.canvas.height * this.spectrumPercent / 100.0);

    this.gradient = this.ctx.createLinearGradient(0, 0, 0, this.spectrumHeight);
    for (var i = 0; i < this.colormap.length; i++) {
        var c = this.colormap[this.colormap.length - 1 - i];
        this.gradient.addColorStop(i / this.colormap.length,
            "rgba(" + c[0] + "," + c[1] + "," + c[2] + ", 1.0)");
    }
}

Spectrum.prototype.resize = function() {
    var width = this.canvas.clientWidth;
    var height = this.canvas.clientHeight;

    if (this.canvas.width != width ||
        this.canvas.height != height) {
        this.canvas.width = width;
        this.canvas.height = height;
        this.updateSpectrumRatio();
    }

    if (this.axes.width != width ||
        this.axes.height != this.spectrumHeight) {
        this.axes.width = width;
        this.axes.height = this.spectrumHeight;
        this.updateAxes();
    }

}

Spectrum.prototype.setSpectrumPercent = function(percent) {
    if (percent >= 0 && percent <= 100) {
        this.spectrumPercent = percent;
        this.updateSpectrumRatio();
    }
}

Spectrum.prototype.incrementSpectrumPercent = function() {
    if (this.spectrumPercent + this.spectrumPercentStep <= 100) {
        this.setSpectrumPercent(this.spectrumPercent + this.spectrumPercentStep);
    }
}

Spectrum.prototype.decrementSpectrumPercent = function() {
    if (this.spectrumPercent - this.spectrumPercentStep >= 0) {
        this.setSpectrumPercent(this.spectrumPercent - this.spectrumPercentStep);
    }
}

Spectrum.prototype.toggleColor = function() {
    this.colorindex++;
    if (this.colorindex >= colormaps.length)
        this.colorindex = 0;
    this.colormap = colormaps[this.colorindex];
    this.updateSpectrumRatio();
}

Spectrum.prototype.setRange = function(min_db, max_db) {
    this.min_db = min_db;
    this.max_db = max_db;
    this.updateAxes();
}

Spectrum.prototype.rangeUp = function() {
    this.setRange(this.min_db - 5, this.max_db - 5);
}

Spectrum.prototype.rangeDown = function() {
    this.setRange(this.min_db + 5, this.max_db + 5);
}

Spectrum.prototype.rangeIncrease = function() {
    this.setRange(this.min_db - 5, this.max_db + 5);
}

Spectrum.prototype.rangeDecrease = function() {
    if (this.max_db - this.min_db > 10)
        this.setRange(this.min_db + 5, this.max_db - 5);
}

Spectrum.prototype.setCenterHz = function(hz) {
    this.centerHz = hz;
    this.updateAxes();
}

Spectrum.prototype.setSpanHz = function(hz) {
    this.spanHz = hz;
    this.updateAxes();
}

Spectrum.prototype.setAveraging = function(num) {
    if (num >= 0) {
        this.averaging = num;
        this.alpha = 2 / (this.averaging + 1)
    }
}

Spectrum.prototype.incrementAveraging = function() {
    this.setAveraging(this.averaging + 1);
}

Spectrum.prototype.decrementAveraging = function() {
    if (this.averaging > 0) {
        this.setAveraging(this.averaging - 1);
    }
}

Spectrum.prototype.setPaused = function(paused) {
    this.paused = paused;
}

Spectrum.prototype.togglePaused = function() {
    this.setPaused(!this.paused);
}

Spectrum.prototype.setMaxHold = function(maxhold) {
    this.maxHold = maxhold;
    this.binsMax = undefined;
}

Spectrum.prototype.toggleMaxHold = function() {
    this.setMaxHold(!this.maxHold);
}

Spectrum.prototype.toggleFullscreen = function() {
    if (!this.fullscreen) {
        if (this.canvas.requestFullscreen) {
            this.canvas.requestFullscreen();
        } else if (this.canvas.mozRequestFullScreen) {
            this.canvas.mozRequestFullScreen();
        } else if (this.canvas.webkitRequestFullscreen) {
            this.canvas.webkitRequestFullscreen();
        } else if (this.canvas.msRequestFullscreen) {
            this.canvas.msRequestFullscreen();
        }
        this.fullscreen = true;
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        this.fullscreen = false;
    }
}

Spectrum.prototype.onKeypress = function(e) {
    if (e.key == " ") {
        this.togglePaused();
    } else if (e.key == "f") {
        this.toggleFullscreen();
    } else if (e.key == "c") {
        this.toggleColor();
    } else if (e.key == "ArrowUp") {
        this.rangeUp();
    } else if (e.key == "ArrowDown") {
        this.rangeDown();
    } else if (e.key == "ArrowLeft") {
        this.rangeDecrease();
    } else if (e.key == "ArrowRight") {
        this.rangeIncrease();
    } else if (e.key == "s") {
        this.incrementSpectrumPercent();
    } else if (e.key == "w") {
        this.decrementSpectrumPercent();
    } else if (e.key == "+") {
        this.incrementAveraging();
    } else if (e.key == "-") {
        this.decrementAveraging();
    } else if (e.key == "m") {
        this.toggleMaxHold();
    }
}

function Spectrum(id, options) {
    // Handle options
    this.centerHz = (options && options.centerHz) ? options.centerHz : 1500;
    this.spanHz = (options && options.spanHz) ? options.spanHz : 0;
    this.wf_size = (options && options.wf_size) ? options.wf_size : 0;
    this.wf_rows = (options && options.wf_rows) ? options.wf_rows : 1024;
    this.spectrumPercent = (options && options.spectrumPercent) ? options.spectrumPercent : 0;
    this.spectrumPercentStep = (options && options.spectrumPercentStep) ? options.spectrumPercentStep : 0;
    this.averaging = (options && options.averaging) ? options.averaging : 0;
    this.maxHold = (options && options.maxHold) ? options.maxHold : false;

    // Setup state
    this.paused = false;
    this.fullscreen = false;
    this.min_db = 0;
    this.max_db = 70;
    this.spectrumHeight = 0;

    // Colors
    this.colorindex = 0;
    this.colormap = colormaps[2];

    // Create main canvas and adjust dimensions to match actual
    this.canvas = document.getElementById(id);
    this.canvas.height = this.canvas.clientHeight;
    this.canvas.width = this.canvas.clientWidth;
    this.ctx = this.canvas.getContext("2d");
    this.ctx.fillStyle = "white";
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

    // Create offscreen canvas for axes
    this.axes = document.createElement("canvas");
    this.axes.height = 1; // Updated later
    this.axes.width = this.canvas.width;
    this.ctx_axes = this.axes.getContext("2d");

    // Create offscreen canvas for waterfall
    this.wf = document.createElement("canvas");
    this.wf.height = this.wf_rows;
    this.wf.width = this.wf_size;
    this.ctx_wf = this.wf.getContext("2d");

    // Trigger first render
    this.setAveraging(this.averaging);
    this.updateSpectrumRatio();
    this.resize();
}
