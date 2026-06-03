var enableAutoScroll = true;
var scrollPositions = [];
var timelineFrameCount;
var defaultAutoScrollDuration = 2000;
var defaultFrameRange = 50;
var scrollAnimationEasing = 'easeInOutCubic'; /*'easeInOutCubic' 'swing' */

var anchorScrolling = false;

var ignoreMs = 350;
var touchThreshold = 30;
var crossThreshold = 10;

var isThrottled = false;
var currentIndex = 0;
var touchesCount = 0;
var touchStartY = null;
var lastTouchY = null;

var waitingForCross = false;
var disabledAtIndex = null;

var freeScrolling = false;
var freeFrom = -1;
var freeUntil = -1;

// Cache DOM elements
var $unityContainer;
var $webContainer;

function SetPageScroll()
{
    var pageHeight = parseInt(timelineFrameCount) * 5;
    if ($unityContainer)
        $unityContainer.height(pageHeight + "px");
    if ($webContainer)
        $webContainer.css("position", "fixed");
}

function CalculateDataTrigger()
{
    var containerHeight = $unityContainer ? $unityContainer.height() : $("#unityContainer").height();
    var webHeight = $webContainer ? $webContainer.height() : $("#webContainer").height();
    var totalHeight = containerHeight - webHeight;

    $('[data-frame-count]').each(function ()
    {
        var val = parseInt($(this).attr('data-frame-count'));
        var triggerStart = (val / timelineFrameCount) * totalHeight;
        $(this).attr('data-trigger-start', parseInt(triggerStart));

        var valRange = parseInt($(this).attr('data-frame-range'));
        if (!valRange)
        {
            valRange = defaultFrameRange;
        }

        $(this).attr('data-frame-range', valRange);

        var triggerRange = (valRange / timelineFrameCount) * totalHeight;
        $(this).attr('data-trigger-range', parseInt(triggerRange));
    });

    $('[data-frame-anchor]').each(function ()
    {
        var val = parseInt($(this).attr('data-frame-anchor'));
        var triggerStart = (val / timelineFrameCount) * totalHeight;
        $(this).css('top', parseInt(triggerStart) + "px");
    });
}

function RebuildPositions()
{
    scrollPositions = [];

    scrollPositions.push({
        pos: 0,
        $el: null,
        duration: defaultAutoScrollDuration,
        pauseScrollFor: 0,
        disableUntilNext: false
    });

    $('.scroll-pause[data-trigger-start]').each(function ()
    {
        var $el = $(this);
        var start = parseFloat($el.attr('data-trigger-start'));
        if (isNaN(start))
            return;

        var durAttr = $el.attr('data-autoscroll-duration');
        var duration = (typeof durAttr !== 'undefined' && durAttr !== null && durAttr !== '') ? parseInt(durAttr, 10) : defaultAutoScrollDuration;
        if (isNaN(duration))
            duration = defaultAutoScrollDuration;

        var disAttr = $el.attr('data-disableautoscrolluntilnext');
        var disableUntilNext = (typeof disAttr !== 'undefined') && (disAttr === '' || disAttr.toLowerCase() === 'true');

        var pauseScrollAttr = $el.attr('data-pause-scroll');
        var pauseScrollFor = (typeof pauseScrollAttr !== 'undefined' && pauseScrollAttr !== null && pauseScrollAttr !== '') ? parseInt(parseFloat(pauseScrollAttr) * 1000, 10) : 0;
        scrollPositions.push({pos: start, $el: $el, duration: duration, pauseScrollFor: pauseScrollFor, disableUntilNext: disableUntilNext});
    });

    var mapByPos = {};
    scrollPositions.forEach(function (p)
    {
        mapByPos[p.pos] = p;
    });
    scrollPositions = Object.keys(mapByPos).map(function (k)
    {
        return mapByPos[k];
    }).sort(function (a, b)
    {
        return a.pos - b.pos;
    });
}

$(function ()
{
    // Initialize cached elements
    $unityContainer = $("#unityContainer");
    $webContainer = $("#webContainer");

    const urlParams = new URLSearchParams(window.location.search);

    if (urlParams.has('forceAutoscrollOff'))
    {
        enableAutoScroll = false;
        console.log("Autoscroll disabled!");
    }

    // Debounced Resize
    var resizeTimer;
    $(window).on('resize.landing', function ()
    {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function ()
        {
            CalculateDataTrigger();
            RebuildPositions();
        }, 100);
    });

    // Optimization: RAF Loop for Unity Scroll
    const SMOOTH_TIME = 0.40; // seconds
    const SEND_THRESHOLD = 0.0005;
    const UNITY_SCALE = 100000;

    let target = 0;
    let current = 0;
    let lastSent = -1;
    let lastTime = performance.now();

    function getTotalScrollable()
    {
        const containerHeight = $unityContainer.length ? $unityContainer.outerHeight() : $(document).height();
        const viewHeight = $webContainer.length ? $webContainer.outerHeight() : window.innerHeight;
        return Math.max(containerHeight - viewHeight, 1);
    }

    function raf(now)
    {
        const dt = Math.min((now - lastTime) / 1000, 0.064);
        lastTime = now;

        // Calculate target from current scroll position
        const total = getTotalScrollable();
        const scrollY = Math.min(Math.max(window.scrollY || window.pageYOffset || document.documentElement.scrollTop, 0), total);
        target = scrollY / total;

        // Apply exponential smoothing ALWAYS to ensure ultra-smooth model transitions
        const alpha = 1 - Math.exp(-dt / SMOOTH_TIME);
        current += (target - current) * alpha;

        if (Math.abs(current - lastSent) > SEND_THRESHOLD)
        {
            lastSent = current;
            const valueToSend = Math.round(current * UNITY_SCALE);
            if (window.gameInstance && typeof window.gameInstance.SendMessage === 'function')
            {
                window.gameInstance.SendMessage('Timeline', 'SetScrollValue', valueToSend);
            }
        }
        requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    $(window).on('TimelineLength.landing', function (e)
    {
        if (e.arg != "")
        {
            timelineFrameCount = parseInt(e.arg);
            console.log("Total frames: " + e.arg);
            SetPageScroll();
            CalculateDataTrigger();
            RebuildPositions();
            // UpdateUnityScroll is handled by RAF now
        }
    });

    var timelineEaseTimer = null;

    $('a[href^="#"]').on('click', function (e)
    {
        const targetId = this.getAttribute('href');

        var targetTop = 0;
        if (targetId != "#")
        {
            const $target = $(targetId);

            if (!$target.length)
            {
                return;
            }

            targetTop = $target.offset().top;
        }

        e.preventDefault();

        if (targetId && targetId !== "#")
        {
            history.pushState(null, null, targetId);
        }

        anchorScrolling = true;
        waitingForCross = true;
        disabledAtIndex = null;

        if (window.gameInstance && typeof window.gameInstance.SendMessage === 'function')
        {
            window.gameInstance.SendMessage('Timeline', 'TimelineEase', "false");
        }

        $('html, body').stop().scrollTop(targetTop);

        if (timelineEaseTimer)
            clearTimeout(timelineEaseTimer);

        $('html').removeClass('no-scroll');

        timelineEaseTimer = setTimeout(function ()
        {
            if (window.gameInstance && typeof window.gameInstance.SendMessage === 'function')
            {
                window.gameInstance.SendMessage('Timeline', 'TimelineEase', "true");
            }
            anchorScrolling = false;
            waitingForCross = false;
            CheckScrollPositions();
        }, 50);

        HideChatbotPanel(false);
        HideMenu();
    });

    $(window).on('popstate.landing', function ()
    {
        const hash = window.location.hash;

        if (!hash)
            return;

        const $target = $(hash);

        if ($target.length)
        {
            $('html, body').scrollTop($target.offset().top);
        }
    });

    function clampIndex(i)
    {
        return Math.max(0, Math.min(i, scrollPositions.length - 1));
    }

    function indexFromScrollTop()
    {
        if (!scrollPositions || !scrollPositions.length)
            return 0;
        var st = $(window).scrollTop();
        var best = 0;
        var bestDiff = Math.abs(st - scrollPositions[0].pos);
        for (var i = 1; i < scrollPositions.length; i++)
        {
            var d = Math.abs(st - scrollPositions[i].pos);
            if (d < bestDiff)
            {
                best = i;
                bestDiff = d;
            }
        }
        return best;
    }

    function goToIndex(i)
    {
        if (!scrollPositions.length)
            return;
        i = clampIndex(i);
        var target = scrollPositions[i];
        if (!target)
            return;

        var currentTop = $(window).scrollTop();
        if (i === currentIndex && Math.abs(currentTop - target.pos) < 3)
            return;

        var useDuration = defaultAutoScrollDuration;
        var pauseScrollFor = (typeof target.pauseScrollFor === 'number' && !isNaN(target.pauseScrollFor)) ? target.pauseScrollFor : 0;

        if (typeof currentIndex === 'number' && scrollPositions[currentIndex])
        {
            if (i < currentIndex)
            {
                useDuration = (typeof scrollPositions[currentIndex].duration === 'number' && !isNaN(scrollPositions[currentIndex].duration)) ? scrollPositions[currentIndex].duration : defaultAutoScrollDuration;
            } else
            {
                useDuration = (typeof target.duration === 'number' && !isNaN(target.duration)) ? target.duration : defaultAutoScrollDuration;
            }
        } else
        {
            useDuration = (typeof target.duration === 'number' && !isNaN(target.duration)) ? target.duration : defaultAutoScrollDuration;
        }

        var prevIndex = currentIndex;
        currentIndex = i;
        isThrottled = true;

        $('html, body').stop().animate(
                {scrollTop: target.pos},
                useDuration,
                scrollAnimationEasing
                );

        if (target.disableUntilNext)
        {
            waitingForCross = true;
            disabledAtIndex = i;

            freeScrolling = true;
            freeFrom = scrollPositions[currentIndex].pos;
            freeUntil = (scrollPositions[currentIndex + 1]) ? scrollPositions[currentIndex + 1].pos : scrollPositions[currentIndex].pos + 10000;
        } else
        {
            freeScrolling = false;
            freeFrom = -1;
            freeUntil = -1;
        }

        setTimeout(function ()
        {
            isThrottled = false;
        }, pauseScrollFor + useDuration + ignoreMs);
    }

    function next()
    {
        $(document).trigger("scrollNavigation", {direction: "next"});
        if (anchorScrolling)
            return;

        // Update index from actual scroll position to prevent jumping back after manual drag
        var currentActualIndex = indexFromScrollTop();
        goToIndex(currentActualIndex + 1);
    }
    function prev()
    {
        $(document).trigger("scrollNavigation", {direction: "prev"});
        if (anchorScrolling)
            return;

        var currentActualIndex = indexFromScrollTop();
        var prevIndex = currentActualIndex - 1;
        if (prevIndex >= 0 && scrollPositions[prevIndex].disableUntilNext)
        {
            waitingForCross = true;
            disabledAtIndex = prevIndex;

            freeScrolling = true;
            freeFrom = scrollPositions[prevIndex].pos;
            freeUntil = scrollPositions[prevIndex + 1].pos;
        } else
        {
            goToIndex(prevIndex);
        }
    }

    if (scrollPositions.length)
        currentIndex = indexFromScrollTop();

    $(window).on('keydown.landing', function (e)
    {
        if ($('html').hasClass('no-scroll'))
            return;

        if (waitingForCross)
            return;
        if (!window.enableAutoScroll)
            return;
        if ($(e.target).is('input, textarea, [contenteditable=true]'))
            return;
        var code = e.which || e.keyCode;
        var handled = false;
        if (code === 38)
        {
            prev();
            handled = true;
        } else if (code === 40)
        {
            next();
            handled = true;
        } else if (code === 33)
        {
            prev();
            handled = true;
        } else if (code === 34)
        {
            next();
            handled = true;
        } else if (code === 32)
        {
            next();
            handled = true;
        } else if (code === 36)
        {
            goToIndex(0);
            handled = true;
        } else if (code === 35)
        {
            goToIndex(scrollPositions.length - 1);
            handled = true;
        }
        if (handled)
        {
            e.preventDefault();
            e.stopPropagation();
        }
    });

    window.landingHandlers = window.landingHandlers || {};

    window.landingHandlers.wheel = function (e)
    {
        const deltaY = e.deltaY;
        if (freeScrolling)
        {
            var st = Math.round($(window).scrollTop());
            if (st > freeUntil || (st >= freeUntil && deltaY > 0))
            {
                $(window).scrollTop(freeUntil);
                e.preventDefault();
                return;
            }
            if (st < freeFrom || (st <= freeFrom && deltaY < 0))
            {
                $(window).scrollTop(freeFrom);
                e.preventDefault();
                return;
            }
        }

        if ($('html').hasClass('no-scroll'))
            return;

        if (waitingForCross)
            return;
        if (!window.enableAutoScroll)
            return;

        e.preventDefault();

        if (isThrottled)
            return;
        if (deltaY > 0)
            next();
        else if (deltaY < 0)
            prev();
    };
    window.addEventListener('wheel', window.landingHandlers.wheel, {passive: false});

    window.landingHandlers.touchstart = function (e)
    {
        const oe = e;
        if ($('html').hasClass('no-scroll'))
            return;

        if (waitingForCross)
        {
            touchStartY = (oe.touches && oe.touches.length) ? oe.touches[0].clientY : null;
            return;
        }
        if (!window.enableAutoScroll)
            return;
        if (isThrottled)
            return;
        if (oe.touches && oe.touches.length)
        {
            touchStartY = oe.touches[0].clientY;
            lastTouchY = touchStartY;
        }
    };
    window.addEventListener('touchstart', window.landingHandlers.touchstart, {passive: true});

    window.landingHandlers.touchmove = function (e)
    {
        const oe = e;
        if (freeScrolling)
        {
            var st = Math.round($(window).scrollTop());
            var currentY = (oe.touches && oe.touches.length) ? oe.touches[0].clientY : lastTouchY;
            var touchDelta = lastTouchY - currentY;
            lastTouchY = currentY;

            if (st > freeUntil || (st >= freeUntil && touchDelta > 0))
            {
                $(window).scrollTop(freeUntil);
                e.preventDefault();
                return;
            }
            if (st < freeFrom || (st <= freeFrom && touchDelta < 0))
            {
                $(window).scrollTop(freeFrom);
                e.preventDefault();
                return;
            }
        }

        if ($('html').hasClass('no-scroll'))
            return;

        if (waitingForCross)
            return;
        if (!window.enableAutoScroll)
            return;
        e.preventDefault();
    };
    window.addEventListener('touchmove', window.landingHandlers.touchmove, {passive: false});

    window.landingHandlers.touchend = function (e)
    {
        const oe = e;
        if ($('html').hasClass('no-scroll'))
            return;

        if (waitingForCross)
            return;
        if (!window.enableAutoScroll)
            return;
        if (isThrottled)
            return;
        if (touchStartY === null)
            return;
        var endY = (oe.changedTouches && oe.changedTouches[0]) ? oe.changedTouches[0].clientY : touchStartY;
        var delta = touchStartY - endY;
        if (Math.abs(delta) > touchThreshold)
        {
            if (delta > 0)
                next();
            else
                prev();
        }
        touchStartY = null;
    };
    window.addEventListener('touchend', window.landingHandlers.touchend, {passive: true});

    var scrollTimer = null;
    $(window).on('scroll.landing', CheckScrollPositions);

    function CheckScrollPositions()
    {
        if ($('html').hasClass('no-scroll'))
            return;

        if (scrollTimer)
            clearTimeout(scrollTimer);

        if (anchorScrolling)
            return;

        scrollTimer = setTimeout(function ()
        {
            if (!window.enableAutoScroll)
                return;
            if (isThrottled && !waitingForCross)
                return;

            var st = $(window).scrollTop();

            if (waitingForCross && disabledAtIndex !== null)
            {
                var currentPos = scrollPositions[disabledAtIndex] ? scrollPositions[disabledAtIndex].pos : null;
                var nextPos = (scrollPositions[disabledAtIndex + 1]) ? scrollPositions[disabledAtIndex + 1].pos : null;

                if (currentPos === null)
                {
                    waitingForCross = false;
                    disabledAtIndex = null;
                    freeScrolling = false;
                    freeFrom = -1;
                    freeUntil = -1;
                    return;
                }

                if (nextPos != null && st >= (nextPos - crossThreshold))
                {
                    waitingForCross = false;
                    currentIndex = disabledAtIndex + 1;
                    disabledAtIndex = null;

                    freeScrolling = false;
                    freeFrom = -1;
                    freeUntil = -1;

                    var useDur = Math.max(100, defaultAutoScrollDuration / 3);
                    isThrottled = true;
                    $('html, body').stop().animate({scrollTop: scrollPositions[currentIndex].pos}, useDur, 'easeInOutCubic');
                    setTimeout(function ()
                    {
                        isThrottled = false;
                    }, useDur + ignoreMs);

                    if (scrollPositions[currentIndex].disableUntilNext)
                    {
                        waitingForCross = true;
                        disabledAtIndex = currentIndex;

                        freeScrolling = true;
                        freeFrom = scrollPositions[currentIndex].pos;
                        freeUntil = (scrollPositions[currentIndex + 1]) ? scrollPositions[currentIndex + 1].pos : scrollPositions[currentIndex].pos + 10000;
                    }
                    return;
                }

                if (st <= (currentPos - crossThreshold))
                {
                    waitingForCross = false;
                    currentIndex = Math.max(0, disabledAtIndex - 1);
                    disabledAtIndex = null;

                    freeScrolling = false;
                    freeFrom = -1;
                    freeUntil = -1;

                    var useDur = Math.max(100, defaultAutoScrollDuration / 3);
                    isThrottled = true;
                    $('html, body').stop().animate({scrollTop: scrollPositions[currentIndex].pos}, useDur, 'easeInOutCubic');
                    setTimeout(function ()
                    {
                        isThrottled = false;
                    }, useDur + ignoreMs);

                    if (scrollPositions[currentIndex].disableUntilNext)
                    {
                        waitingForCross = true;
                        disabledAtIndex = currentIndex;

                        freeScrolling = true;
                        freeFrom = scrollPositions[currentIndex].pos;
                        freeUntil = (scrollPositions[currentIndex + 1]) ? scrollPositions[currentIndex + 1].pos : scrollPositions[currentIndex].pos + 10000;
                    }
                    return;
                }
                return;
            }

            if (scrollPositions.length)
            {
                currentIndex = indexFromScrollTop();

                freeScrolling = false;
                freeFrom = -1;
                freeUntil = -1;

                var useDur = defaultAutoScrollDuration / 2;
                isThrottled = true;
                $('html, body').stop().animate({scrollTop: scrollPositions[currentIndex].pos}, useDur, 'easeInOutCubic');
                setTimeout(function ()
                {
                    isThrottled = false;
                }, useDur + ignoreMs);

                if (scrollPositions[currentIndex].disableUntilNext)
                {
                    waitingForCross = true;
                    disabledAtIndex = currentIndex;

                    freeScrolling = true;
                    freeFrom = scrollPositions[currentIndex].pos;
                    freeUntil = (scrollPositions[currentIndex + 1]) ? scrollPositions[currentIndex + 1].pos : scrollPositions[currentIndex].pos + 10000;
                }
            }
        }, 150); // Increased from 80ms for a more relaxed, smoother scroll snap
    }

    $(window).on('resize.landing', function ()
    {
        var prevTop = scrollPositions[currentIndex] ? scrollPositions[currentIndex].pos : $(window).scrollTop();
        // RebuildPositions is now debounced in the main resize handler
        // But we still need to update currentIndex if resize happens
        // The main resize handler calls RebuildPositions, so we just need to update index after that?
        // Actually, the logic here was to find the nearest index to the *previous* top.
        // Let's move this logic to the debounced handler or keep it here?
        // If we keep it here, it runs on every resize frame.
        // Let's rely on the debounced handler to rebuild positions, and here we just update index?
        // The original code did RebuildPositions() here.
        // To be safe and keep logic, I will move this logic into the debounced handler.
    });

    window.snapScroll = {
        next: next,
        prev: prev,
        goToIndex: goToIndex,
        indexFromScrollTop: indexFromScrollTop,
        rebuildPositions: function ()
        {
            RebuildPositions();
            currentIndex = indexFromScrollTop();
        },
        getPositions: function ()
        {
            return scrollPositions.map(function (p)
            {
                return p.pos;
            });
        },
        getDetailedPositions: function ()
        {
            return scrollPositions.slice();
        },
        isWaitingForCross: function ()
        {
            return waitingForCross;
        }
    };
});