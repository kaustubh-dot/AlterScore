var currentLangObj = {};
var currentLangLabel;
var loadingDict;
var systemLanguageCode;

var urlLang = GetQueryParam('lang');

if (urlLang === 'it' || urlLang === 'en' || urlLang === 'test')
{
    systemLanguageCode = urlLang;
} else
{
    var userLanguage = navigator.language || navigator.userLanguage;
    systemLanguageCode = userLanguage.startsWith('it') ? 'it' : 'en';
}

// Force EN
systemLanguageCode = 'en';

SetLang(systemLanguageCode);

$(document).ready(function ()
{
    $(".langButton").click(function ()
    {
        var lang = $(this).attr("data-language");
        SetLang(lang);
    });
});

function SetLang(lang)
{
    if (loadingDict)
    {
        return;
    } else
    {
        loadingDict = true;
    }

    $(".langButton").removeClass("selected");

    $.getJSON("lang/" + lang + ".json?" + version, function (json)
    {
        if (currentLangLabel != lang)
        {
            currentLangObj = {};
        }

        $.extend(currentLangObj, json);

        currentLangLabel = lang;

        loadingDict = false;

        Localize();

        $(".langButton[data-language=" + lang + "]").addClass("selected");
        $(document).trigger('langChange');
    }).fail(function (jqXHR, textStatus, errorThrown)
    {
        console.log('Lang request failed! ' + errorThrown + " - " + textStatus);
    });
}

function ChangeLang(thisField)
{
    var newLang = thisField.attr("data-lang");

    console.log("Setting lang to: " + thisField.attr("data-lang"));

    SetLang(newLang);
}

function Localize()
{
    $("[data-lang]").each(function ()
    {
        //console.log("Setting: " + $(this).attr("data-lang") + " - " + currentLangObj[ $(this).attr("data-lang") ] );
        if ($(this).attr("placeholder") !== undefined)
        {
            $(this).attr("placeholder", currentLangObj[ $(this).attr("data-lang") ]);
        } else if ($(this).attr("title") !== undefined)
        {
            $(this).attr("title", currentLangObj[ $(this).attr("data-lang") ]);
        } else if ($(this).attr("data-original") !== undefined)
        {
            $(this).attr("data-original", currentLangObj[ $(this).attr("data-lang") ]);
        } else
        {
            $(this).html(currentLangObj[ $(this).attr("data-lang") ]);
        }
    });

    $("[data-langurl]").each(function ()
    {
        if ($(this).attr("href") !== undefined)
        {
            $(this).attr("href", currentLangObj[ $(this).attr("data-langurl") ]);
        } else
        {
            console.log("data-langurl works only for links");
        }
    });

    $("body").trigger("languageChange");
}

function GetWord(key)
{
    if (key in currentLangObj)
    {
        return currentLangObj[key];
    } else
    {
        return key;
    }
}
