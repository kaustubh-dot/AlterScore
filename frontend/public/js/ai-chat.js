$(document).ready(function ()
{
    $("#chatbotBtn").click(function ()
    {
        if ($(this).hasClass("chatbotOpened"))
        {
            HideChatbotPanel(true);
        } else
        {
            ShowChatbotPanel();
        }
    });

    $("#chatbotQuestion").on("keydown change", function (e)
    {
        if (e.key === "Enter" || e.keyCode === 13)
        {
            e.preventDefault();
            ChatbotSendQuestion();
        }
    });

    $("#chatbotContactsQuestion").on("keydown change", function (e)
    {
        if (e.key === "Enter" || e.keyCode === 13)
        {
            e.preventDefault();
            ChatbotContactsSendQuestion();
        }
    });

    $("#chatbotSend").click(function ()
    {
        ChatbotSendQuestion();
    });

    $("#chatbotContactsSend").click(function ()
    {
        ChatbotContactsSendQuestion();
    });

    /*
     $("#chatbotContactsQuestion").on("focus", function ()
     {
     $('html').addClass('no-scroll');
     });
     
     $("#chatbotContactsQuestion").on("blur", function ()
     {
     $('html').removeClass('no-scroll');
     });
     */

    $("#chatbotContactsBtn").click(function ()
    {
        if ($(this).hasClass("opened"))
        {
            HideContactsReachUs();
        } else
        {
            ShowContactsReachUs();
        }
    });

    $("#chatbotAIBtn").click(function ()
    {
        if ($(this).hasClass("opened"))
        {
            HideChatbotContacts();
        } else
        {
            ShowChatbotContacts();
        }
    });

    $("#chatbotBackToSelection").click(function ()
    {
        HideChatbotContacts();
        HideContactsReachUs();
    });

    $('#reachus-form').on('submit', function (e)
    {
        e.preventDefault();

        $('#reachus-responseMessage').text("");

        var first_name = $('#reachus-first_name').val();
        var last_name = $('#reachus-last_name').val();
        var email = $('#reachus-email').val();
        var message = $('#reachus-message').val();
        var privacy = $('#reachus-gdpr').is(':checked') ? 1 : 0;

        if (!privacy)
        {
            $('#reachus-responseMessage').text('You must accept the privacy policy.');
            return;
        }


        $("#reachus-loading").fadeIn();
        $.ajax({
            url: './form.php',
            type: 'POST',
            data: {
                first_name: first_name,
                last_name: last_name,
                email: email,
                message: message,
                privacy: privacy
            },
            success: function (response)
            {
                console.log("Reachus Form message: " + response);

                if (response.success)
                {
                    $('#reachus-first_name').val("");
                    $('#reachus-email').val("");
                    $('#reachus-message').val("");
                    $("#reachus-form").css("opacity", 0);
                    $("#reachus-success").fadeIn();
                    window.setEmail?.(email, "Reach Us", "Contact", first_name, last_name);
                } else
                {
                    $('#reachus-responseMessage').text(response.message);
                }

            },
            error: function ()
            {
                $('#reachus-responseMessage').text('An error occurred.');
            },
            complete: function ()
            {
                $("#reachus-loading").fadeOut();
            }
        });
    });
});

function HideChatbotBtn()
{
    $("#chatbotBtn").fadeOut();
}
function ShowChatbotBtn()
{
    $("#chatbotBtn").fadeIn();
}

function ShowChatbotPanel()
{
    $('html').addClass('no-scroll');
    $("#chatbotBtn").addClass("chatbotOpened");
    $("#chatbotPanel, #chatbotMessages, #chatbotSingleMessage").fadeIn();
    $("#chatbotQuestion").focus();
}
function HideChatbotPanel(unlockScroll)
{
    $("#chatbotBtn").removeClass("chatbotOpened");
    $("#chatbotPanel, #chatbotMessages, #chatbotSingleMessage").fadeOut(function ()
    {
        if (unlockScroll)
            $('html').removeClass('no-scroll');
    });
}


function htmlToExcerpt(html, maxLength = 100) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const text = doc.body.textContent || "";

  const normalized = text.replace(/\s+/g, " ").trim();

  if (normalized.length <= maxLength) {
    return normalized;
  }

  return normalized.slice(0, maxLength).trimEnd() + "…";
}

var chatbotMessages = $("#chatbotMessages");
var chatbotSingleMessage = $("#chatbotSingleMessage");
var chatbotContactsMessage = $("#chatbotContactsMessage");
var mdParser = new LemonMDStreamingParser();

var savedSession = sessionStorage.getItem("lemon_session");
var client = new LemonClient({
    url: "wss://lemon-engine.sidewave.it/wss",
    sessionId: savedSession,

    onInit(sessionId)
    {
        console.log("Sessione:", sessionId);
        sessionStorage.setItem("lemon_session", sessionId);
        window._paq = window._paq || [];
        if(!window.session_initialized){
            window.session_initialized = true;
            _paq.push(['setCustomDimension', 1, sessionId]);
            _paq.push(['trackEvent', 'AI', 'SessionInit', sessionId]);
        }
    },

    onHistory(messages)
    {
        if (chatbotMessages.length != 0)
            chatbotMessages.innerHTML = "";
        if (chatbotSingleMessage.length != 0)
            chatbotSingleMessage.innerHTML = "";
        messages.forEach(msg => {
            if (msg.channel === "website")
            {
                chatbotMessages.css("visibility", "visible");
                chatbotSingleMessage.css("visibility", "visible");

                if (msg.role === "assistant")
                {
                    AppendChatbotMessage(msg.role, mdParser.parseStatic(msg.message));
                } else
                {
                    AppendChatbotMessage(msg.role, msg.message);
                }
            } else
            {
                // se il canale non è website dovrebbe essere "contacts" che però non ha history
            }

        });
    },

    onTextChunk(id, chunk, fullText)
    {
        const result = mdParser.push(id, chunk);
        if (chatbotInContacts)
        {
            StreamChatbotContactsAnswer(id, result.html);
        } else
        {
            StreamChatbotAnswer(id, result.html);
        }
    },

    onResponseComplete(id, fullText)
    {
        const result = mdParser.complete(id, fullText);
        FinalizeChatbotAnswer(id, result.html);

        window._paq = window._paq || [];
        _paq.push(['trackEvent', 'AI', 'AgentMessage', htmlToExcerpt(result.html)]);
    },

    onThinking(id)
    {
        //showThinking(id);
    },

    onError(id, message)
    {
        if (chatbotInContacts)
        {
            chatbotContactsMessage.html(message);
        } else
        {
            AppendChatbotMessage("error", message);
        }
    }
});

client.connect();


var chatbotInContacts = false;
var disabledByChatbot = false;
;

function ChatbotSendQuestion()
{
    chatbotMessages.css("visibility", "visible");
    chatbotSingleMessage.css("visibility", "visible");

    const text = $("#chatbotQuestion").val().trim();
    if (!text)
        return;

    AppendChatbotMessage("user", text);
    client.send(text, "website");

    disabledByChatbot = true;
    $("#chatbotQuestion").attr("disabled", "disabled");

    $("#chatbotTextThinking").show();
    $("#chatbotTextOpened").hide();
    //chatbotSingleMessage.html("<img src='images/Mobius100.gif'>");

    window._paq = window._paq || [];
    _paq.push(['trackEvent', 'AI', 'UserMessage', text]);
}

function ChatbotContactsSendQuestion()
{
    const text = $("#chatbotContactsQuestion").val().trim();
    if (!text)
        return;

    client.send(text, "contacts");

    disabledByChatbot = true;
    $("#chatbotContactsQuestion").attr("disabled", "disabled");

    chatbotContactsMessage.html("<img src='images/Mobius100.gif'>");

    window._paq = window._paq || [];
    _paq.push(['trackEvent', 'AI', 'UserMessageContacts', text]);
}

function AppendChatbotMessage(role, text)
{
    const div = $("<div>");
    div.addClass("chatMsg");
    div.html(text);

    div.addClass(role);

    if (chatbotMessages.length != 0)
        chatbotMessages.append(div);
    if (chatbotMessages.length != 0)
        chatbotMessages.scrollTop(chatbotMessages[0].scrollHeight);
}

function StreamChatbotAnswer(id, html)
{
    let el = $("#msg-" + id);

    if (el.length === 0)
    {
        el = $("<div>", {
            id: "msg-" + id,
            class: "chatMsg assistant streaming"
        });

        chatbotMessages.append(el);

        chatbotSingleMessage.html("");
        chatbotSingleMessage.append(el);
    }

    el.html(html);
    if (chatbotMessages.length != 0)
        chatbotMessages.scrollTop(chatbotMessages[0].scrollHeight);
    if (chatbotSingleMessage.length != 0)
        chatbotSingleMessage.scrollTop(chatbotSingleMessage[0].scrollHeight);
}
function FinalizeChatbotAnswer(id, html)
{
    let el = $("#msg-" + id);
    if (el)
    {
        el.html(html);
        el.removeClass("streaming");
    }

    disabledByChatbot = false;

    $("#chatbotTextThinking").hide();

    ChatbotTextNext();
    $("#chatbotTextOpened").show();

    if (chatbotInContacts)
    {
        el.find("p").each(function ()
        {
            if (!this.dataset.original)
            {
                this.dataset.original = this.innerHTML;
            }
        });

        setTimeout(function ()
        {
            $("#chatbotContactsQuestion").val("").removeAttr("disabled");

            $("#chatbotContactsQuestion").focus();
        }, 100);
    } else
    {
        setTimeout(function ()
        {
            $("#chatbotQuestion").val("").removeAttr("disabled");

            $("#chatbotQuestion").focus();
        }, 100);
    }
}

var chatbotTexts = ["START WITH A QUESTION", "GET IN TOUCH", "REACH US", "DISCOVER MORE", "ASK ANYTHING"];
var currentChatbotText = 0;
function ChatbotTextNext()
{
    currentChatbotText++;
    if (currentChatbotText >= chatbotTexts.length)
        currentChatbotText = 0;
    $("#chatbotTextOpened").text(chatbotTexts[currentChatbotText]);
}

function StreamChatbotContactsAnswer(id, html)
{
    let el = $("#msg-" + id);

    if (el.length === 0)
    {
        el = $("<div>", {
            id: "msg-" + id,
            class: "chatMsg assistant streaming"
        });

        chatbotContactsMessage.html("");
        chatbotContactsMessage.append(el);
    }

    el.html(html);
}


function showThinking(id)
{
    let el = document.getElementById(`msg-${id}`);
    if (!el)
    {
        el = document.createElement("div");
        el.id = `msg-${id}`;
        el.className = "msg msg-assistant streaming";
        chatbotMessages.appendChild(el);
    }
    el.textContent = "assistant: sta pensando...";
}



function InContacts()
{
    $("#clientsButton, #clientsLine").fadeOut();
    $("#spaceNavigation").hide();
}

function OutContacts()
{
    $("#clientsButton, #clientsLine").fadeIn();
    $("#spaceNavigation").show();

    HideChatbotContacts();
    HideContactsReachUs();
}

function ShowChatbotContacts()
{
    $(".contactsBtns, #sendy-form-footer-wrapper").fadeOut();
    $("#chatbotBackToSelection").fadeIn();
    $('html').addClass('no-scroll');
    $("#chatbotAIBtn").addClass("opened");
    $("#chatbotContactsPanel").fadeIn();
    $("#chatbotContactsMessage").fadeIn();

    chatbotInContacts = true;
}

function HideChatbotContacts()
{
    $(".contactsBtns, #sendy-form-footer-wrapper").fadeIn();
    $("#chatbotBackToSelection").fadeOut();
    $('html').removeClass('no-scroll');
    $("#chatbotAIBtn").removeClass("opened");
    $("#chatbotContactsPanel").fadeOut();
    $("#chatbotContactsMessage").fadeOut();

    chatbotInContacts = false;

}


function ShowContactsReachUs()
{
    $(".contactsBtns, #sendy-form-footer-wrapper").fadeOut();
    $("#chatbotBackToSelection").fadeIn();
    $('html').addClass('no-scroll');
    $("#chatbotContactsBtn").addClass("opened");
    $("#chatbotReachUsPanel").fadeIn();

    $("#reachus-form").css("opacity", 1);
    $("#reachus-success").hide();
}

function HideContactsReachUs()
{
    $(".contactsBtns, #sendy-form-footer-wrapper").fadeIn();
    $("#chatbotBackToSelection").fadeOut();
    $('html').removeClass('no-scroll');
    $("#chatbotContactsBtn").removeClass("opened");
    $("#chatbotReachUsPanel").fadeOut();
}
