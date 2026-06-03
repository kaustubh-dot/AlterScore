/* global gtag, CookieConsent */

function updateGtagConsent()
{
    if (typeof CookieConsent === 'undefined')
    {
        console.log("ADBlock is active");
        return;
    }

    if (typeof gtag !== "undefined")
    {
        gtag('consent', 'update', {
            'analytics_storage': CookieConsent.acceptedService('analytics_storage', 'analytics') ? 'granted' : 'denied'
        });
    }
}

window.addEventListener("load", function ()
{
    // obtain plugin
    if (typeof CookieConsent === 'undefined')
    {
        console.log("ADBlock is active");
        return;
    }


    // Enable dark mode
    document.documentElement.classList.add('cc--darkmode');

    CookieConsent.run({
        guiOptions: {
            consentModal: {
                layout: "cloud inline",
                position: "bottom left",
                equalWeightButtons: true,
                flipButtons: false
            },
            preferencesModal: {
                layout: "box",
                position: "right",
                equalWeightButtons: true,
                flipButtons: false
            }
        },
        onFirstConsent: () => {
            updateGtagConsent();
        },
        onConsent: () => {
            updateGtagConsent();
        },
        onChange: () => {
            updateGtagConsent();
        },
        categories: {
            necessary: {
                enabled: true, // this category is enabled by default
                readOnly: true  // this category cannot be disabled
            },
            analytics: {
                autoClear: {
                    cookies: [
                        {
                            name: /^_ga/, // regex: match all cookies starting with '_ga'
                        },
                        {
                            name: '_gid', // string: exact cookie name
                        }
                    ]
                },
                services: {
                    'analytics_storage': {
                        label: 'Enables storage (such as cookies) related to analytics e.g. visit duration.',
                    }
                }
            }
        },
        language: {
            default: (typeof systemLanguageCode !== 'undefined') ? systemLanguageCode : 'en',

            translations: {
                'it': {
                    consentModal: {
                        title: 'Cookies!',
                        description: 'Utilizziamo i cookie per migliorare la tua esperienza e per fini analitici.',
                        acceptAllBtn: 'Accetta tutti',
                        acceptNecessaryBtn: 'Rifiuta tutti',
                        showPreferencesBtn: 'Gestisci Preferenze',
                        footer: "<a href='/cookie-policy' target='_blank'>COOKIE POLICY</a>"
                    },
                    preferencesModal: {
                        title: 'Preferenze Cookie',
                        savePreferencesBtn: 'Salva preferenze',
                        acceptAllBtn: 'Accetta tutti',
                        acceptNecessaryBtn: 'Rifiuta tutti',
                        closeIconLabel: 'Chiudi',
                        sections: [
                            {
                                title: "Utilizzo dei Cookie",
                                description: "Utilizziamo i cookie per garantire le funzionalità di base del sito web e per migliorare la vostra esperienza online."
                            },
                            {
                                title: 'Prestazioni e Analitiche',
                                description: 'Questi cookie raccolgono informazioni sulle modalità di utilizzo del nostro sito web. Tutti i dati sono anonimizzati e non possono essere utilizzati per identificare l\'utente.',
                                linkedCategory: 'analytics',

                                cookieTable: {
                                    headers: {
                                        name: "Nome",
                                        domain: "Servizio",
                                        description: "Descrizione",
                                        expiration: "Scadenza"
                                    },
                                    body: [
                                        {
                                            name: "_ga",
                                            domain: "Google Analytics",
                                            description: "Cookie impostato da <a href=\"https://business.safety.google/adscookies/\">Google Analytics</a>",
                                            expiration: "Scade dopo 12 giorni"
                                        },
                                        {
                                            name: "_gid",
                                            domain: "Google Analytics",
                                            description: "Cookie impostato da <a href=\"https://business.safety.google/adscookies/\">Google Analytics</a>",
                                            expiration: "Sessione"
                                        }
                                    ]
                                }
                            },
                            {
                                title: 'Ulteriori informazioni',
                                description: 'Per ogni domanda in relazione ai nostri cookie ed alle tue scelte <a class="cc-link" href="#contact">contattaci</a>.',
                            }
                        ]
                    }
                },
                'en': {
                    consentModal: {
                        title: 'We use cookies!',
                        description: 'WE USE COOKIES TO IMPROVE YOUR EXPERIENCE AND COLLECT ANALYTICS DATA.',
                        acceptAllBtn: 'Accept all',
                        acceptNecessaryBtn: 'Reject all',
                        showPreferencesBtn: 'Manage Preferences',
                        footer: "<a href='/cookie-policy' target='_blank'>COOKIE POLICY</a>"
                    },
                    preferencesModal: {
                        title: 'Cookie preferences',
                        savePreferencesBtn: 'Save preferences',
                        acceptAllBtn: 'Accept all',
                        acceptNecessaryBtn: 'Reject all',
                        closeIconLabel: 'Close',
                        sections: [
                            {
                                title: "Cookie usage",
                                description: "We use cookies to ensure the basic functionalities of the website and to enhance your online experience."
                            },
                            {
                                title: 'Performance and Analytics',
                                description: 'These cookies collect information about how you use our website. All of the data is anonymized and cannot be used to identify you.',
                                linkedCategory: 'analytics',

                                cookieTable: {
                                    headers: {
                                        name: "Name",
                                        domain: "Service",
                                        description: "Description",
                                        expiration: "Expiration"
                                    },
                                    body: [
                                        {
                                            name: "_ga",
                                            domain: "Google Analytics",
                                            description: "Cookie set by <a href=\"https://business.safety.google/adscookies/\">Google Analytics</a>",
                                            expiration: "Expires after 12 days"
                                        },
                                        {
                                            name: "_gid",
                                            domain: "Google Analytics",
                                            description: "Cookie set by <a href=\"https://business.safety.google/adscookies/\">Google Analytics</a>",
                                            expiration: "Session"
                                        }
                                    ]
                                }
                            },
                            {
                                title: 'More information',
                                description: 'For any queries in relation to our policy on cookies and your choices, please <a class="cc-link" href="#contact">contact us</a>.'
                            }
                        ]
                    }
                }
            }
        }
    });
}
);
