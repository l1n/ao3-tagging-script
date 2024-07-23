// ==UserScript==
// @name         AO3 Collection and Work Info Extractor
// @namespace    http://tampermonkey.net/
// @version      0.3
// @description  Open works from an AO3 collection, extract info, and copy to clipboard
// @match        https://archiveofourown.org/collections/*
// @match        https://archiveofourown.org/works/*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_setClipboard
// ==/UserScript==

(function() {
    'use strict';

    // Function to extract work info
    function extractInfo() {
        let info = JSON.parse(GM_getValue('currentWorkInfo', '{}'));

        // Add or update fields from the work page
        Object.assign(info, {
            Team: GM_getValue('teamName', 'Unknown'),
            Stage: 'Board 3',
            Art: 'FALSE',
            Podfic: 'FALSE',
            Fic: 'TRUE',
            Points: '',
            Wordcount: document.querySelector('dd.words')?.textContent.trim() || '',
            Link: window.location.href,
            Rating: '',
            Ship: '',
            Warning: document.querySelector('dd.warning.tags a')?.textContent.trim() || '',
        });

        // Map Rating
        let ratingText = document.querySelector('dd.rating.tags a')?.textContent.trim() || '';
        info.Rating = (ratingText === 'Mature' || ratingText === 'Explicit') ? 'M-E Rated' : 'G-T Rated';

        // Map Ship (Category)
        let categoryText = document.querySelector('dd.category.tags a')?.textContent.trim() || '';
        switch(categoryText) {
            case 'Gen': info.Ship = 'Gen'; break;
            case 'F/F': info.Ship = 'F/F'; break;
            case 'M/M': info.Ship = 'M/M'; break;
            case 'F/M': info.Ship = 'F/M'; break;
            default: info.Ship = 'Other/Multi';
        }

        // Extract tags
        let authorNotes = document.querySelector('.preface .notes')?.textContent || '';
        let tagLine = authorNotes.split('\n').reverse().find(line =>
            line.toLowerCase().includes('tags')
        ) || '';
        let tags = tagLine.replace(/^tags:?\s*/i, '').split(/,\s*/).map(tag => tag.trim());
        for (let i = 0; i < 10; i++) {
            info[`Tag${i+1}`] = tags[i] || '';
        }
        /* let tags = Array.from(document.querySelectorAll('dd.freeform.tags a')).map(tag => tag.textContent.trim());
        for (let i = 0; i < 10; i++) {
            info[`Tag${i+1}`] = tags[i] || '';
        } */

        // Check for art or podfic
        let summary = document.querySelector('div.summary .userstuff')?.textContent.toLowerCase() || '';
        if (summary.includes('art')) {
            info.Art = 'TRUE';
            info.Fic = 'FALSE';
            // info.Points = '2';
        } else if (summary.includes('podfic')) {
            info.Podfic = 'TRUE';
            info.Fic = 'FALSE';
            // info.Points = '2';
        }

        // Format as tab-separated values
        let fields = ['Team', 'Stage', 'Art', 'Podfic', 'Fic', 'Points', 'Wordcount', 'Creator1', 'Creator2', 'Creator3', 'Recipient', 'Link', 'Rating', 'Ship', 'Warning'];
        for (let i = 1; i <= 10; i++) {
            fields.push(`Tag${i}`);
        }
        let tsv = fields.map(field => info[field]).join('\t');

        // Copy to clipboard
        GM_setClipboard(tsv);

        // Show popup notification
        showNotification('Work info copied to clipboard! Paste into the spreadsheet, and then close this window and hit next on the collection to continue.');

        // Signal that this work is processed
        window.opener.postMessage('workProcessed', '*');
    }

    // Function to show notification
    function showNotification(message) {
        let notification = document.createElement('div');
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '10px';
        notification.style.left = '50%';
        notification.style.transform = 'translateX(-50%)';
        notification.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
        notification.style.color = 'white';
        notification.style.padding = '10px';
        notification.style.borderRadius = '5px';
        notification.style.zIndex = '10000';
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Function to open all works
    function openAllWorks() {
        // Extract team name from collection title
        let collectionTitle = document.querySelector('h2.heading')?.textContent.trim() || '';
        let teamName = collectionTitle.includes('Team') ? collectionTitle.split('Team')[1].trim() : '';

        // Save team name for use in the other script
        GM_setValue('teamName', teamName);

        // Get all work elements
        let workElements = document.querySelectorAll('.header.module');

        // Extract info for each work
        let workInfos = Array.from(workElements).map(workElement => {
            if (workElement.textContent.includes('(Draft)')) {
                return {link: ""}; // Skip drafts
            }
            let link = workElement.querySelector('h4.heading a')?.href || '';
            let creatorRecipientText = workElement.querySelector('h5.heading')?.textContent.trim() || '';

            // Split creator and recipient
            let [creator, recipient] = creatorRecipientText.split('for').map(s => s.trim());

            // Remove "for" from recipient if present
            recipient = recipient ? recipient.replace(/^for\s+/, '') : '';

            // Split multiple creators
            let creators = creator.split(/\s*,\s*/);

            return {
                link: link,
                Creator1: creators[0] || '',
                Creator2: creators[1] || '',
                Creator3: creators[2] || '',
                Recipient: recipient
            };
        }).filter(work => work.link !== "skip" && work.link.length);

        // Save work infos
        GM_setValue('remainingWorks', JSON.stringify(workInfos));

        // Open first work
        if (workInfos.length > 0) {
            openNextWork();
        }

        alert(`Processing ${workInfos.length} works. Team name set to: ${teamName}`);
    }

    // Function to open next work
    function openNextWork() {
        let remainingWorks = JSON.parse(GM_getValue('remainingWorks', '[]'));
        if (remainingWorks.length > 0) {
            let nextWork = remainingWorks.shift();
            GM_setValue('remainingWorks', JSON.stringify(remainingWorks));
            GM_setValue('currentWorkInfo', JSON.stringify(nextWork));
            console.log(`opening ${JSON.stringify(nextWork)}`);
            window.open(nextWork.link, 'ao3work');
        } else {
            alert('All works processed!');
        }
    }

    // Check if we're on a collection page or a work page
    if (window.location.pathname.includes('/collections/')) {
        // We're on a collection page
        let button = document.createElement('button');
        button.textContent = 'Process All Works';
        button.style.position = 'fixed';
        button.style.top = '10px';
        button.style.right = '10px';
        button.style.zIndex = '9999';
        button.addEventListener('click', openAllWorks);
        document.body.appendChild(button);
    } else if (window.location.pathname.includes('/works/')) {
        // We're on a work page
        extractInfo();
    }

    // Listen for messages from work pages
    window.addEventListener('message', function(event) {
        if (event.data === 'workProcessed') {
            if (confirm('Work processed. Open next work?')) {
                openNextWork();
            }
        }
    });
})();
