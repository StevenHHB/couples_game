document.addEventListener("DOMContentLoaded", function() {

    function searchUsers() {
        const query = document.getElementById('searchInput').value;
        
        fetch(`/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'query': query
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = ''; // clear previous results

            if (data && data.length > 0) {
                data.forEach(user => {
                    let div = document.createElement('div');
                    div.className = 'result-item';

                    let nameDiv = document.createElement('div');
                    nameDiv.className = 'result-name';
                    nameDiv.textContent = user.username;

                    let addButton = document.createElement('button');
                    addButton.textContent = 'Send Request';
                    addButton.onclick = function() {
                        sendCoupleRequest(user.id); 
                    };

                    div.appendChild(nameDiv);
                    div.appendChild(addButton);
                    resultsDiv.appendChild(div);
                });
            } else {
                resultsDiv.innerHTML = '<p>No users found.</p>';
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error.message);
        });
    }

    function sendCoupleRequest(userId) {
        const currentUserId = document.getElementById('currentUserId').value;

        fetch('/add_couple', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'user1_id': currentUserId,
                'user2_id': userId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.message) {
                alert(data.message);
                window.location.href = '/profile';
            } else {
                alert(data.error);
            }
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error.message);
        });
    }

    // Attach the searchUsers function to the search button
    document.querySelector("button").addEventListener("click", searchUsers);

});
