

const url = 'http://127.0.0.1:8000/';
const defaultEmbodySource = '/static/img/dummy_600.png';

$(document).ready(function() {

    // Init draw variables

    var clickX = new Array();
    var clickY = new Array();
    var clickRadius = new Array();
    var clickDrag = new Array();
    var paint;
    var width = 0;
    var height = 0;
    var drawRadius=13
    var default_embody=false
    var points = []
    var imageId = null;

    try {
        var canvas = $("#embody-canvas")
        var canvasInfo = $(".canvas-info")
        var context = document.getElementById("embody-canvas").getContext("2d");

        //var oldimg = document.getElementById("baseImage");
        var img = $('.embody-image.selected-embody')[0]
        var instruction = $('.embody-question.selected-embody')[0]

        img.onload = function() {
            drawImage()
        }

    } catch (e) {
        console.log(e)
        if (e instanceof TypeError) {
            return
        }
    }

    function drawImage() {

        newImage = new Image();
        newImage.src =  img.src

        newImage.onload = function() {
            imageId = img.id
            width = newImage.width;
            height = newImage.height;
            context.canvas.height = height
            context.canvas.width = width
            context.drawImage(newImage, 0, 0);
            $(img).hide()
        }
    }

    drawImage()

    // Click handlers
    canvas.mousedown(function(e){

        //var mouseX = e.pageX - this.offsetLeft;
        //var mouseY = e.pageY - this.offsetTop;

        var parentOffset = $(this).offset(); 
        var mouseX = e.pageX - parentOffset.left;
        var mouseY = e.pageY - parentOffset.top;

        paint = true;

        if (pointInsideBaseImage([mouseX, mouseY])) {
            addClick(mouseX, mouseY);
            redraw();
        }
    });

    canvas.mousemove(function(e){

        var parentOffset = $(this).offset(); 
        var mouseX = e.pageX - parentOffset.left;
        var mouseY = e.pageY - parentOffset.top;

        if (paint && pointInsideBaseImage([mouseX, mouseY])){
            addClick(mouseX, mouseY, true);
            redraw();
        }
    });

    canvas.bind('touchmove', function(e){
        e.preventDefault()

        //var mouseX = e.touches[0].pageX - this.offsetLeft;
        //var mouseY = e.touches[0].pageY - this.offsetTop;

        var parentOffset = $(this).offset(); 
        var mouseX = e.touches[0].pageX - parentOffset.left;
        var mouseY = e.touches[0].pageY - parentOffset.top;

        [mouseX, mouseY] = scaleClickCoordinates($(this)[0], mouseX, mouseY)

        if (paint && pointInsideBaseImage([mouseX, mouseY])){
            addClick(mouseX, mouseY, true);
            redraw();
        }
    });

    canvas.bind('touchstart', function(e){
        e.preventDefault()

        var parentOffset = $(this).offset(); 
        var mouseX = e.touches[0].pageX - parentOffset.left;
        var mouseY = e.touches[0].pageY - parentOffset.top;

        paint = true;

        [mouseX, mouseY] = scaleClickCoordinates($(this)[0], mouseX, mouseY)

        if (pointInsideBaseImage([mouseX, mouseY])) {
            addClick(mouseX, mouseY);
            redraw();
        }
    });

    function scaleClickCoordinates(element, x, y) { 
        var clientHeight = element.clientHeight;
        var trueHeight = element.height 
        var clientWidth = element.clientWidth;
        var trueWidth = element.width 

        if (clientHeight !== trueHeight) {
            y = y * (trueHeight / clientHeight)
            x = x * (trueWidth / clientWidth)
        }

        return [x,y]

    };

    canvas.mouseup(function(e){
        paint = false;
    });

    canvas.mouseleave(function(e){
        paint = false;
    });


    $("#embody-canvas").bind('DOMMouseScroll', changeBrushSize)
    // DOMMouseScroll is only for firefox
    
    function changeBrushSize(event) {
        event.preventDefault()

        // Change brush size
        if (event.originalEvent.detail >= 0){
            if (drawRadius >= 13) {
                drawRadius -= 5; 
            }
        } else {
            if (drawRadius <= 13) {
                drawRadius += 5; 
            }
        }

        // Show brush size to user
        if (drawRadius == 8) {
            canvasInfo.html("small brush")
        } else if (drawRadius == 13) {
            canvasInfo.html("normal brush")
        } else if (drawRadius == 18) {
            canvasInfo.html("large brush")
        }
    }

    $(".clear-button").on('click', function() {
        clearCanvas()
    })

    $(".next-page").click(function() {
        saveData()
    })


    function saveData() {

        points.push({
            id: imageId,
            x: clickX,
            y: clickY,
            r: clickRadius,
            width: width,
            height: height
        })

        clickX = []
        clickY = []
        clickRadius = []

        if ($(img).hasClass('last-embody')) {
            // Send data to db
            try {
                points = JSON.stringify(points)
                $("#canvas-data").val(points);
                $("#canvas-form").submit();
            } catch(e) {
                console.log(e)
            }

        } else {
            // Show next picture
            img = img.nextElementSibling

            $(instruction).addClass("hidden")
            $(instruction.nextElementSibling).removeClass("hidden")

            try {
                drawImage()
            } catch(e) {
                console.log(e)
            }
        }
    }

    // Draw methods
    function addClick(x, y, dragging=false) {
        clickX.push(x);
        clickY.push(y);
        clickRadius.push(drawRadius);
        clickDrag.push(dragging);
    }

    function drawPoint(x, y, radius) {
        context.beginPath();
        context.arc(x, y, radius, 0, 2 * Math.PI, false);
        context.fill()
    }

    function isWhite(color) {
        return (color === 255) ? true : false;
    }

    // Method for checking if cursor is inside human body before creating brush stroke
    function pointInsideBaseImage(point) {

        if (default_embody) {
            var imageData = context.getImageData(point[0], point[1],1,1)

            startR = imageData.data[0];
            startG = imageData.data[1];
            startB = imageData.data[2];

            return (isWhite(startB) && isWhite(startG) && isWhite(startR)) ? false : true;
        } else {
            return true
        }
    }

    function redraw() {

        lastX = clickX[clickX.length - 1]
        lastY = clickY[clickY.length - 1]

        // Opacity (there was 0.2 opacity in the old version):
        context.globalAlpha = 0.15
        
        // Gradient:
        var gradient = context.createRadialGradient(lastX, lastY, 1, lastX, lastY, drawRadius);


        gradient.addColorStop(0, "rgba(255,0,0,1)");
        gradient.addColorStop(1, "rgba(255,0,0,0.1)");


        context.fillStyle = gradient

        // Draw circle with gradient
        drawPoint(lastX, lastY, drawRadius)


        // Draw mask on default image
        
        if (img.getAttribute('src') === defaultEmbodySource) {
            drawMaskToBaseImage()
        }

    }

    function drawMaskToBaseImage() {
        var img = document.getElementById("baseImageMask");
        context.globalAlpha = 1
        context.drawImage(img, 0, 0);
    }

    function drawBaseImage() {
        var width = img.width;
        var height = img.height;

        context.canvas.height = height
        context.canvas.width = width

        context.drawImage(img, 0, 0);
        $(img).hide()
    }

    function clearCanvas() {
        context.clearRect(0, 0, context.canvas.width, context.canvas.height);
        drawBaseImage()

        // Remove saved coordinates
        clickX = []
        clickY = []
        clickDrag = []
    }
            
});