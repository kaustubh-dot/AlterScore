/* global createUnityInstance */

var gameInstance;
var version = "0.1";

var buildUrl = "Build/";

var dataname = "Sidewave_WebGL_260421.data.br";   // Unity sostituirà qui il nome reale
var isGzip = dataname.indexOf(".gz") !== -1;
var isBrotli = dataname.indexOf(".br") !== -1;

var buildName = dataname;
if (isGzip)
{
    buildName = dataname.replace('.data.gz', '');
} else if (isBrotli)
{
    buildName = dataname.replace('.data.br', '');
} else
{
    buildName = dataname.replace('.data', '');
}

var compressionExt = '';
if (isGzip)
{
    compressionExt = '.gz';
} else if (isBrotli)
{
    compressionExt = '.br';
}

var isMobile = false;
if (/Mobile|iPhone|iPad|iPod|Android/i.test(navigator.userAgent))
{
    document.body.className = "isMobile";
    isMobile = true;
}

if (isMobile)
{
    buildName += "_astc";
} else
{
    buildName += "_dxt";
}

var loaderUrl = buildUrl + buildName + ".loader.js";

var config = {
    dataUrl: buildUrl + buildName + ".data" + compressionExt,
    frameworkUrl: buildUrl + buildName + ".framework.js",
    codeUrl: buildUrl + buildName + ".wasm" + compressionExt,
    streamingAssetsUrl: "StreamingAssets",
    companyName: "AlterScore",
    productName: "AlterScore-Landing",
    productVersion: "0.1"
};

var container = document.querySelector("#unityContainer");
var canvas = document.querySelector("#webContainer");
var progressBarFull = document.querySelector("#unity-progress-bar-full");

SetUnityCanvasScale();

var script = document.createElement("script");
script.src = loaderUrl;
script.onload = () => {
    createUnityInstance(canvas, config, (progress) => {
        progressBarFull.style.width = 100 * progress + "%";
        var premiumFill = document.querySelector(".loader-progress-fill");
        if (premiumFill) {
            premiumFill.style.width = 100 * progress + "%";
        }
        //console.log("Loading: " + 100 * progress + "%" );
    }).then((unityInstance) => {
        gameInstance = unityInstance;

        if (gameInstance.Module.SystemInfo.mobile)
        {
            gameInstance.SendMessage("zController", "DisableFluidFx");
        } else {
            gameInstance.SendMessage("zController", "EnableFluidFx");
        }

        if (window.location.hash)
        {
            ScrollToHash();
        } else {
            ShowUnityWebGL();
        }
    }).catch((message) => {
        alert(message);
    });
};

document.body.appendChild(script);

function ShowUnityWebGL()
{
    document.querySelector("#unityProgress").style.display = "none";
    $("#webContainer").delay(50).css("opacity", 1);
    $("#loopLoader").delay(50).fadeOut();
    $(".showAfterLoading").fadeIn();
    $(".hideAfterLoading").fadeOut();
}

var waitScrollHash = false;

function ScrollToHash()
{
    var id = window.location.hash;
    if ($(id).length)
    {
        var targetTop = $(id).offset().top;

        anchorScrolling = true;
        waitingForCross = true;

        if (window.gameInstance && typeof window.gameInstance.SendMessage === 'function')
        {
            window.gameInstance.SendMessage('Timeline', 'TimelineEase', "false");
        }


        $('html, body').stop().scrollTop(targetTop);
        
		waitScrollHash = true;
	} else {
        ShowUnityWebGL();
    }
}

function SetUnityCanvasScale()
{
    var devicePixelRatio = 1;
    if (PageWidth() > 2560)
    {
        devicePixelRatio = 2560 / PageWidth();
    }

    try {
        Object.defineProperty(window, 'devicePixelRatio', {
            get: function() { return devicePixelRatio; },
            configurable: true
        });
    } catch (e) {
        try {
            window.devicePixelRatio = devicePixelRatio;
        } catch (err) {
            console.warn("Could not set window.devicePixelRatio:", err);
        }
    }
}

function PageWidth()
{
    return Math.max(
            document.body.scrollWidth,
            document.body.offsetWidth,
            document.documentElement.offsetWidth,
            document.documentElement.clientWidth
            );
}

function GetQueryParam(name)
{
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

// Interaction with Unity
$(document).ready(function ()
{
    $("#webContainer").click(function ()
    {
        if (gameInstance && gameInstance != null)
        {
            gameInstance.SendMessage("zController", "HasFocus");
        }
    });
    $("body").click(function (e)
    {
        if ($(e.target).attr('id') != "webContainer" && gameInstance && gameInstance != null)
        {
            gameInstance.SendMessage("zController", "LostFocus");
        }
    });

    $(window).on('HoverOn.landing', function ()
    {
        $("#unityContainer").addClass("hovering");
    });
    $(window).on('HoverOff.landing', function ()
    {
        $("#unityContainer").removeClass("hovering");
    });
	
	$(window).on('WebGLSafeDraw.landing', function ()
    {
        if (waitScrollHash)
        {
            if (gameInstance && typeof gameInstance.SendMessage === 'function')
            {
                gameInstance.SendMessage('Timeline', 'TimelineEase', "true");
            }
            anchorScrolling = false;
            waitingForCross = false;

            ShowUnityWebGL();
        }
    });

    $(window).on('resize.landing', function ()
    {
        if (gameInstance && gameInstance != null)
        {
            //gameInstance.SendMessage("zController", "Resized");
            SetUnityCanvasScale();
        }
    });

    function SimulateClick(event)
    {
        // Ignore clicks on menu button (or its children)
        if (event.target.closest("#menuBtn") || event.target.closest("a") || event.target.closest("#menuPanel") || event.target.closest("#clientsButton"))
        {
            return;
        }
		
		if( $("#menuBtn").hasClass("menuOpened")) return;

        var rect = $("#webContainer")[0].getBoundingClientRect();
        var mouseX = event.clientX - rect.left;
        var mouseY = event.clientY - rect.top;

        var x = mouseX * window.devicePixelRatio;
        var y = (rect.height - mouseY) * window.devicePixelRatio;

        if (gameInstance && gameInstance != null)
        {
            gameInstance.SendMessage("zController", "ClickAt", parseInt(x) + "/" + parseInt(y));
        }
    }
    $(document).on('click.landing', SimulateClick);
});

function EventDispatcher(eventName)
{
    var evt = $.Event(eventName);
    evt.state = eventName;
    evt.arg = null;

    $(window).trigger(evt);
}

function EventDispatcherWithArgument(eventName, argument)
{
    var evt = $.Event(eventName);
    evt.state = eventName;
    evt.arg = argument;

    $(window).trigger(evt);
}
