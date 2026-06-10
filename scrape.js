(function exportScopeTabToCSV() {
    const nameTables = document.querySelectorAll('table.sc-22e980a7-0');
    const statTables = document.querySelectorAll('table.sc-a3ead467-0');

    if (nameTables.length === 0 || statTables.length === 0) {
        alert("Couldn't find the match tables. Make sure you are on the specific match details page.");
        return;
    }

    // 1. UNIQUE MATCH ID (Extracted from URL)
    const matchIdMatch = window.location.pathname.match(/matches\/(\d+)/);
    const matchId = matchIdMatch ? matchIdMatch[1] : Math.floor(Date.now() / 1000);

    // 2. EXTRACT SCORE
    let matchScore = "Unknown";
    try {
        // Find the colon element that sits between the scores
        const colonElement = Array.from(document.querySelectorAll('span')).find(s => s.innerText.trim() === ':');
        if (colonElement && colonElement.parentElement) {
            // Grab all numbers from the score wrapper
            const numbers = colonElement.parentElement.innerText.match(/\d+/g);
            if (numbers && numbers.length >= 2) {
                matchScore = `${numbers[0]}-${numbers[1]}`;
            }
        }
    } catch(e) { console.error("Could not find score", e); }
    
    // 3. EXTRACT HEADERS
    const headerCells = statTables[0].querySelectorAll('thead th');
    const statHeaders = Array.from(headerCells).map(th => `"${th.innerText.trim().replace(/\n/g, ' ')}"`);

    let csvContent = "data:text/csv;charset=utf-8,";
    // Add Match ID and Score to the headers
    csvContent += `"Match ID","Match Score","Team","Player",${statHeaders.join(",")}\n`;

    // 4. EXTRACT ROW DATA
    for (let i = 0; i < nameTables.length; i++) {
        const nameTable = nameTables[i];
        const statTable = statTables[i];

        let teamName = "Unknown Team";
        const teamElem = nameTable.querySelector('thead th');
        if (teamElem) teamName = teamElem.innerText.split('\n')[0].trim();

        const playerRows = nameTable.querySelectorAll('tbody tr');
        const statRows = statTable.querySelectorAll('tbody tr');

        for (let j = 0; j < playerRows.length; j++) {
            const pRow = playerRows[j];
            const sRow = statRows[j];

            let playerName = "Unknown";
            const profileLink = pRow.querySelector('a[href^="/profile/"]');
            if (profileLink && profileLink.nextElementSibling) {
                playerName = profileLink.nextElementSibling.innerText.trim();
            }

            const stats = Array.from(sRow.querySelectorAll('td')).map(td => {
                return `"${td.innerText.trim().replace(/\n/g, ' ')}"`;
            });

            // Put the Match ID and Score in every row
            const rowData = [
                `"${matchId}"`,
                `"${matchScore}"`,
                `"${teamName}"`,
                `"${playerName}"`,
                ...stats
            ];
            csvContent += rowData.join(",") + "\n";
        }
    }

    // 5. TRIGGER DOWNLOAD WITH UNIQUE NAME
    let tabName = "stats";
    // Find whichever tab currently has the 'checked' attribute
    const activeTab = document.querySelector('button div[checked] span');
    if (activeTab) {
        tabName = activeTab.innerText.trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    }

    const fileName = `match_${matchId}_${tabName}.csv`;

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
})();