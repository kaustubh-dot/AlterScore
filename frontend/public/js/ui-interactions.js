var scrollbarWidth;
var wasScrollable = false;

function ShowMenu()
{
    wasScrollable = !$('html').hasClass('no-scroll');

    $("#menuBtn").addClass("menuOpened");
    $("#menuPanel").fadeIn();

    //HideChatbotPanel(false);
    $("#servicesTunnel p").fadeIn();
    $(".servicesBox").fadeOut();

    $('html').addClass('no-scroll');
}

function HideMenu()
{
    $("#menuBtn").removeClass("menuOpened");
    $("#menuPanel").fadeOut();

    //HideChatbotPanel(false);
    $("#servicesTunnel p").fadeIn();
    $(".servicesBox").fadeOut();

    if (wasScrollable)
    {
        $('html').removeClass('no-scroll');
    }
}

$(document).ready(function ()
{
    $("#menuBtn").click(function ()
    {
        if ($(this).hasClass("menuOpened"))
        {
            HideMenu();
        } else
        {
            ShowMenu();
        }
    });

    $("#menuPanel ul a").click(function ()
    {
        $("#menuBtn").trigger("click");
    });

    $('#portfolioClose').click(function ()
    {
        ClosePortfolioOverlay();
    });

    PrepareTextForAnimations();

    $(document).on("langChange", function ()
    {
        PrepareTextForAnimations();
    });

    // Trigger on .visible
    const observer = new MutationObserver(mutations => {
        mutations.forEach(m => {
            if (m.attributeName === "class" && m.target.classList.contains("visible"))
            {
                $(m.target)
                        .find("p")
                        .each(function ()
                        {
                            scrambleHTMLText(this);
                        });
            }
        });
    });

    $(".scroll-overlay-text").each(function ()
    {
        observer.observe(this, {attributes: true});
    });


    $(window).on('ClickedUseCase', function (e)
    {
        console.log('ClickedUseCase ' + e.arg);
        if (e.arg != "")
        {
            console.log("Show portfolio for: " + e.arg);
            ShowPortfolio(e.arg);
        }
    });
	
	$(window).on('UseCasePositions', function (e)
    {
        if (e.arg != "")
        {
            const obj = JSON.parse(e.arg);
            obj.forEach(el => {
                $("#useCase_"+el.id).css('left', el.x+"px").css('bottom', el.y+"px");
            });
        }
    });

    $(window).on('ServicesBox', function (e)
    {
        if (e.arg != "")
        {
            $("#servicesBox-" + e.arg).fadeIn();
            $("#servicesTunnel p").fadeOut();

            if (isPortrait())
            {
                HideChatbotPanel(false);
                $('html').addClass('no-scroll');
            } else
            {
                HideChatbotPanel(true);
            }
        }
    });

    $(".servicesBox").click(function ()
    {
        $(this).fadeOut();
        $("#servicesTunnel p").fadeIn();
        $('html').removeClass('no-scroll');
    });

    $("#clientsButton").click(function ()
    {
        if ($(this).hasClass('clientsOpen'))
        {
            $("#clientsPopup").fadeOut();
            $(this).removeClass('clientsOpen');
            $('html').removeClass('no-scroll');
            $("#menuBtn").fadeIn();
        } else
        {
            HideChatbotPanel(false);

            $("#clientsPopup").fadeIn();
            $(this).addClass('clientsOpen');
            $('html').addClass('no-scroll');
            $("#menuBtn").fadeOut();
        }
    });

    scrollbarWidth = GetScrollbarWidth();
    $("html").css('--scrollbar-width', scrollbarWidth + 'px');

    $(window).on('resize.landing', function ()
    {
        scrollbarWidth = GetScrollbarWidth();
        $("html").css('--scrollbar-width', scrollbarWidth + 'px');
    });

    const loadingMessages = [
        "Mapping behavioral patterns. The signal is forming.",
        "Calibrating ensemble models. Precision takes a moment.",
        "Rendering the credit landscape. Almost there.",
        "Aligning signal layers. Preparing your experience.",
        "Finalizing the terrain. Just a moment more."
    ];

    LoadingMessages(loadingMessages, 3); // cambia ogni 3 secondi


    LoadPortfolioList();

    $("#portfolioPrev").click(function ()
    {
        if (portfolioNavigation.previous != null)
        {
            ShowPortfolio(portfolioNavigation.previous.id);
        }
    });
    $("#portfolioNext").click(function ()
    {
        if (portfolioNavigation.next != null)
        {
            ShowPortfolio(portfolioNavigation.next.id);
        }
    });




    $('.sendy-form').on('submit', function (e)
    {
        e.preventDefault();
        var $form = $(this);

        var email = $form.find('.sendy-email').val();
        var gdpr = $form.find('input[name="gdpr"]').is(':checked') ? 1 : 0;
        var hp = $form.find('.sendy-hp').val();

        if (!gdpr)
        {
            $form.find('.sendy-title').text('You must accept the privacy policy.');
            return;
        }

        $.ajax({
            url: './php/sendy.php',
            type: 'POST',
            data: {
                email: email,
                gdpr: gdpr,
                hp: hp
            },
            success: function (response)
            {
                console.log("Sendy message: " + response);
                $form.find('.sendy-title').text(response);
                $form.find('.sendy-email').val("");
                window.setEmail?.(email);
            },
            error: function ()
            {
                $form.find('.sendy-title').text('An error occurred.');
            }
        });
    });
});

var loadingTimeout = null;

function LoadingMessages(messages, changeEverySeconds)
{
    let index = 0;
    const $el = $("#loadingMessages span");

    if (!messages || messages.length === 0)
        return;

    $el.text(messages[index]);

    function cycle()
    {
        loadingTimeout = setTimeout(function ()
        {

            $el.fadeOut(400, function ()
            {

                index = (index + 1) % messages.length;
                $el.text(messages[index]).fadeIn(400, function ()
                {
                    cycle(); // richiama solo quando finito
                });

            });

        }, changeEverySeconds * 1000);
    }

    cycle();
}

function StopLoadingMessages()
{
    if (loadingTimeout)
    {
        clearTimeout(loadingTimeout);
        loadingTimeout = null;
    }
}

function PrepareTextForAnimations()
{
    const delayStep = 80; // ms between characters

    $('.scroll-overlay-text h2').each(function ()
    {
        const $h2 = $(this);
        const nodes = $h2.contents();

        let charIndex = 0;
        $h2.empty();

        nodes.each(function ()
        {
            // Preserve <br>
            if (this.nodeType === 1 && this.tagName === 'BR')
            {
                $h2.append('<br>');
                return;
            }

            // Text nodes
            if (this.nodeType === 3)
            {
                const words = this.nodeValue.split(/(\s+)/); // mantiene gli spazi

                words.forEach(word => {
                    if (word.trim() === '')
                    {
                        // spazio normale
                        $h2.append(document.createTextNode(word));
                        return;
                    }

                    // wrapper parola
                    const $wordSpan = $('<span class="word"></span>');

                    for (let i = 0; i < word.length; i++)
                    {
                        const $char = $('<span>', {
                            text: word[i],
                            css: {
                                transitionDelay: (charIndex * delayStep) + 'ms'
                            }
                        });

                        $wordSpan.append($char);
                        charIndex++;
                    }

                    $h2.append($wordSpan);
                });
            }
        });
    });

    // Init
    $(".scroll-overlay-text p").each(function ()
    {
        if (!this.dataset.original)
        {
            this.dataset.original = this.innerHTML;
        }

        // Initial scramble
        const walker = document.createTreeWalker(this, NodeFilter.SHOW_TEXT);
        while (walker.nextNode())
        {
            if (walker.currentNode.textContent.trim())
            {
                walker.currentNode.textContent =
                        walker.currentNode.textContent
                        .split("")
                        .map(() => chars[Math.floor(Math.random() * chars.length)])
                        .join("");
            }
        }
    });
}

function ShowLoading()
{
    $("#loopLoaderOverlay").fadeIn();
}
function HideLoading()
{
    $("#loopLoaderOverlay").fadeOut();
}

var portfolioList;
var portfolioNavigation;
var portfolioFallbackTimeout = null;

window.addEventListener('message', function (e) {
    if (e.data === 'portfolio-video-ready') {
        clearTimeout(portfolioFallbackTimeout);
        setTimeout(function () {
            HideLoading();
            $('#portfolioOverlay').stop().fadeIn(300);
        }, 100);
    }
});
function LoadPortfolioList()
{
    const jsonUrl = `projects/usecases-list.json`;
    $.getJSON(jsonUrl).done(function (data)
    {
        portfolioList = data;
		
		for(var i = 0; i < portfolioList.length; i++  ) {
            var el = portfolioList[i];
            $("#useCasesLabels").append("<div id='useCase_"+el.id+"'><span class='title'>"+el.name+"</span><span class='subtitle'>"+el.subtitle+"</span>");
        }

    }).fail(function (jq, status, err)
    {
        console.error('Failed to load JSON:', status, err);
    });
}

function GetPortfolioNavigationById(id)
{
    const index = portfolioList.findIndex(item => item.id === id);

    if (index === -1)
        return null;

    return {
        previous: portfolioList[index - 1] || null,
        current: portfolioList[index],
        next: portfolioList[index + 1] || null
    };
}

function ShowPortfolio(projectName)
{
    const jsonUrl = `projects/${encodeURIComponent(projectName)}.json`;
    const iframeUrl = `/usecases/${encodeURIComponent(projectName)}`;

    portfolioNavigation = GetPortfolioNavigationById(projectName);

    $("#portfolioNavigation, #portfolioPrev, #portfolioNext").hide();
    if (portfolioNavigation.previous != null)
    {
        $("#portfolioNavigation, #portfolioPrev").show();
    }
    if (portfolioNavigation.next != null)
    {
        $("#portfolioNavigation, #portfolioNext").show();
    }

    // Fade in loader first, then hide the portfolio overlay and clear the iframe
    $("#loopLoaderOverlay").fadeIn(300, function () {
        $('#portfolioOverlay').hide();
        $('#portfolioFrame').attr('src', 'about:blank');

        fetch(jsonUrl, {method: 'HEAD'})
                .then(response => {
                    if (!response.ok)
                    {
                        HideLoading();
                        throw new Error('Project JSON not found');
                    }

                    // Fallback for use cases without video (image-only backgrounds)
                    clearTimeout(portfolioFallbackTimeout);
                    portfolioFallbackTimeout = setTimeout(function () {
                        HideLoading();
                        $('#portfolioOverlay').stop().fadeIn(300);
                    }, 4000);

                    $('#portfolioFrame').attr('src', iframeUrl);
                    $('html').addClass('no-scroll');
                })
                .catch(() => {
                    console.warn(`Project "${projectName}" does not exist.`);
                });
    });
}

function ClosePortfolioOverlay()
{
    $('html').removeClass('no-scroll');

    $('#portfolioOverlay').fadeOut(300, function ()
    {
        $('#portfolioFrame').attr('src', '');
    });
}

var chars = "!<>-_\\/[]{}—=+*^?#@£$€%&§";

function scrambleHTMLText(el)
{
    if (!el.dataset.original)
        return;

    el.innerHTML = el.dataset.original;

    const textNodes = [];
    const walker = document.createTreeWalker(
            el,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode(node)
                {
                    return node.textContent.trim()
                            ? NodeFilter.FILTER_ACCEPT
                            : NodeFilter.FILTER_REJECT;
                }
            }
    );

    while (walker.nextNode())
    {
        const text = walker.currentNode.textContent;
        textNodes.push({
            node: walker.currentNode,
            original: text,
            progress: Array.from(text).map(() => ({
                    end: Math.floor(Math.random() * 20) + 10
                }))
        });
    }

    let frame = 0;

    const interval = setInterval(() => {
        let done = true;

        textNodes.forEach(obj => {
            const {node, original, progress} = obj;

            node.textContent = original
                    .split("")
                    .map((char, i) => {
                        if (char === " ")
                        {
                            return char;
                        }
                        if (frame >= progress[i].end)
                        {
                            return char;
                        }
                        done = false;
                        return chars[Math.floor(Math.random() * chars.length)];
                    })
                    .join("");
        });

        frame++;

        if (done)
        {
            clearInterval(interval);
            el.innerHTML = el.dataset.original; // final clean reset
        }
    }, 30);
}



var tooltipActive = false;

function ShowUseCaseTooltip()
{
    const $tooltip = $("#useCaseTooltip");
    $tooltip.fadeIn(100);
    tooltipActive = true;

    $(document).on("mousemove.tooltip", function (e)
    {
        if (!tooltipActive)
            return;

        const offset = 12;
        $tooltip.css({
            left: e.clientX + offset,
            top: e.clientY + offset
        });
    });
}

function HideUseCaseTooltip()
{
    tooltipActive = false;
    $("#useCaseTooltip").fadeOut(100);
    $(document).off("mousemove.tooltip");
}

function GetScrollbarWidth()
{
    // Creiamo un div temporaneo
    const outer = document.createElement('div');
    outer.style.visibility = 'hidden';
    outer.style.overflow = 'scroll'; // forziamo la scrollbar
    outer.style.width = '100px';
    outer.style.position = 'absolute';
    outer.style.top = '-9999px';
    document.body.appendChild(outer);

    // Creiamo un div interno per misurare la differenza
    const inner = document.createElement('div');
    inner.style.width = '100%';
    outer.appendChild(inner);

    // La larghezza della scrollbar è la differenza tra outer e inner
    const scrollbarWidth = outer.offsetWidth - inner.offsetWidth;

    // Rimuoviamo il div temporaneo
    outer.parentNode.removeChild(outer);

    return scrollbarWidth;
}


function ShowAwardsDesc()
{
    $("#about_awards_label p").css("opacity", 1);
}

function HideAwardsDesc()
{
    $("#about_awards_label p").css("opacity", 0);
}


function InServicesTunnel()
{
    $("#clientsButton, #clientsLine, #chatbotBtn").fadeOut();
}

function OutServicesTunnel()
{
    $("#clientsButton, #clientsLine, #chatbotBtn").fadeIn();
}
