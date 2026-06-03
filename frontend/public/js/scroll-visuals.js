$(document).ready(function ()
{
    const $overlayElements = $(".scroll-overlay, .scroll-overlay-text, .scroll-overlay-list, .scroll-overlay-image");

    let lastScrollY = window.scrollY;
    let lastTime = performance.now();
    let scrollSpeed = 0;

    let ticking = false;
    const SPEED_LIMIT = 2000;
    const TOLERANCE = 300;
    const STOP_DELAY = 120;

    let lastScrollEventTime = performance.now();
    var scrollTimer;
    var navHintDelay = 6000;

    scrollTimer = setTimeout(ShowNavHint, navHintDelay);
    $(window).on('scroll.landing', CheckScrollSpeedAndOverlays);

    function CheckScrollSpeedAndOverlays()
    {
        if ($('html').hasClass('no-scroll'))
            return;

        const now = performance.now();
        const newScrollY = window.scrollY;
        const deltaY = Math.abs(newScrollY - lastScrollY);
        let deltaTime = (now - lastTime) / 1000;

        if (deltaTime <= 0)
            deltaTime = 1 / 1000;

        scrollSpeed = deltaY / deltaTime;

        lastScrollY = newScrollY;
        lastTime = now;
        lastScrollEventTime = now;

        if (!ticking)
        {
            window.requestAnimationFrame(() => {
                CheckScroll();
                ticking = false;
            });
            ticking = true;
        }
    }

    var currentAnchor;
    function CheckScroll()
    {
        $("#spaceNavigation").removeClass("flicker");

        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(ShowNavHint, navHintDelay);

        const now = performance.now();
        const scrollY = window.visualViewport.pageTop || window.scrollY;
        const timeSinceLastScroll = now - lastScrollEventTime;
        const scrollTolerance = 200;

        var lastLateralAnchor;
        $(".anchor").each(function ()
        {
            var lateralAnchorTop = $(this).position().top;
            if (scrollY >= lateralAnchorTop)
            {
                if (lastLateralAnchor == null || lastLateralAnchor.position().top < lateralAnchorTop)
                {
                    lastLateralAnchor = $(this);
                }
            }
        });

        if (lastLateralAnchor != null)
        {
            if (currentAnchor != lastLateralAnchor.attr('id'))
            {
                $("[data-menutarget]").removeClass('active');
                $("[data-menutarget=" + lastLateralAnchor.attr('id') + "]").addClass('active');

                currentAnchor = lastLateralAnchor.attr('id');
                //console.log("Active anchor: " + currentAnchor);
                
                $(document).trigger("navigationUpdate", currentAnchor);
            }
        } else
        {
            $("[data-menutarget]").removeClass('active');
        }


        $overlayElements.each(function ()
        {
            var $overlay = $(this);
            var triggerStart = parseInt($overlay.attr("data-trigger-start"), 10);
            var triggerRange = parseInt($overlay.attr("data-trigger-range"), 10);

            if (scrollY + scrollTolerance >= triggerStart && scrollY <= triggerStart + triggerRange)
            {
                if (!$overlay.hasClass('visible'))
                {
                    $overlay.removeClass("afterScroll");
                    $overlay.addClass("visible");

                    var fnName = $overlay.attr('data-visible-fn');
                    var params = $overlay.attr('data-visible-params');
                    params = params ? JSON.parse(params) : [];

                    if (typeof window[fnName] === 'function')
                    {
                        window[fnName].apply(null, params);
                    }
                }
            } else if ($overlay.hasClass('visible'))
            {
                if (scrollY > triggerStart + triggerRange)
                {
                    $overlay.addClass("afterScroll");

                    var fnName = $overlay.attr('data-hiddenAfter-fn');
                    var params = $overlay.attr('data-hiddenAfter-params');
                    params = params ? JSON.parse(params) : [];

                    if (typeof window[fnName] === 'function')
                    {
                        window[fnName].apply(null, params);
                    }
                } else
                {
                    $overlay.removeClass("afterScroll");

                    var fnName = $overlay.attr('data-hiddenBefore-fn');
                    var params = $overlay.attr('data-hiddenBefore-params');
                    params = params ? JSON.parse(params) : [];

                    if (typeof window[fnName] === 'function')
                    {
                        window[fnName].apply(null, params);
                    }
                }
                $overlay.removeClass("visible");
            } else if (scrollY < triggerStart + triggerRange && $overlay.hasClass('afterScroll'))
            {
                $overlay.removeClass("afterScroll");

                var fnName = $overlay.attr('data-hiddenBefore-fn');
                var params = $overlay.attr('data-hiddenBefore-params');
                params = params ? JSON.parse(params) : [];

                if (typeof window[fnName] === 'function')
                {
                    window[fnName].apply(null, params);
                }
            } else if (scrollY + scrollTolerance >= triggerStart && !$overlay.hasClass('afterScroll'))
            {
                $overlay.addClass("afterScroll");

                var fnName = $overlay.attr('data-hiddenAfter-fn');
                var params = $overlay.attr('data-hiddenAfter-params');
                params = params ? JSON.parse(params) : [];

                if (typeof window[fnName] === 'function')
                {
                    window[fnName].apply(null, params);
                }
            }
        });
    }

    $(".scroll-overlay-origin-list").click(function ()
    {
        if (currentClickOriginListIndex != -1)
        {
            CancelClickOriginList();
        } else
        {
            var str = $(this).attr('id');
            var num = str[str.length - 1];
            ClickOriginList(parseInt(num));
        }
    });

    $(window).on('scroll.landing', function ()
    {
        if (currentClickOriginListIndex != -1)
        {
            CancelClickOriginList();
        }

        if ($(".servicesBox").is(":visible") && !$(".servicesBox").is(":animated"))
        {
            $(".servicesBox").stop(true, true).fadeOut();
            gameInstance.SendMessage("zController", "ClickAt", parseInt(100) + "/" + parseInt(100));
        }
    });

    $(window).on('resize.landing', function ()
    {
        if ($("#originList").is(":visible") && $("#originList").css("opacity") == 1)
        {
            ScrollOriginList(currentOriginListIndex);
        }
    });

    $(document).on('scrollNavigation.landing', function (e, data)
    {
        if ($("#originList").is(":visible") && $("#originList").css("opacity") == 1)
        {
            if (data.direction === "next")
            {
                var nextIndex = currentOriginListIndex + 1;
                ScrollOriginList(nextIndex);
                //console.log("Scroll origin list next " + nextIndex);
            } else if (data.direction === "prev")
            {
                var prevIndex = currentOriginListIndex - 1;
                ScrollOriginList(prevIndex);
                //console.log("Scroll origin list prev " + prevIndex);
            }
        }
    });

    $(".reachus").click(function ()
    {
        gameInstance.SendMessage("zController", "ClickAt", parseInt(100) + "/" + parseInt(100));
    });

    $(window).on('ServicesTunnelUnfreeze.landing', function ()
    {
        $(".servicesBox").fadeOut();
        $("#servicesTunnel p").fadeIn();
    });
});

function ShowNavHint()
{
    $("#spaceNavigation").addClass("flicker");
}

function EnterAboutList(target)
{
    var currentActualIndex = snapScroll.indexFromScrollTop();
    snapScroll.goToIndex(currentActualIndex + target);
}

var currentOriginListIndex = 0;
function ScrollOriginList(index)
{
    currentOriginListIndex = index;

    if (index < 0 || index >= 4)
        return;

    var left = 55 - (index + 2) * 35;
    if (isPortrait())
    {
        left = (index + 2) * -100;
    }
    $("#originList ul").css('left', left + 'vw');

    $('#originList ul li').removeClass('active');
    $('#originList ul li').eq(index + 2).addClass('active');
}

var currentClickOriginListIndex = -1;
function ClickOriginList(index)
{
    currentClickOriginListIndex = index;
    $(".originClickToDiscover").fadeOut();
    $("#originList" + index + " .originSubText").fadeOut();
    $("#originListLabel" + index).css('color', 'transparent');

    $("#originList" + index + " .originListClick").addClass('visible');
    gameInstance.SendMessage("OriginVolume_RED", "SetWeight", 1);
}

function CancelClickOriginList()
{
    $(".originClickToDiscover").fadeIn();
    $("#originList" + currentClickOriginListIndex + " .originSubText").fadeIn();
    $("#originListLabel" + currentClickOriginListIndex).removeAttr('style');

    $("#originList" + currentClickOriginListIndex + " .originListClick").removeClass('visible');
    gameInstance.SendMessage("OriginVolume_RED", "SetWeight", 0);

    currentClickOriginListIndex = -1;
}


function isPortrait()
{
    return $(window).height() > $(window).width();
}