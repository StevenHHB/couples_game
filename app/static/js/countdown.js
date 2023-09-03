document.addEventListener('DOMContentLoaded', function() {
    const timeRemainingElement = document.getElementById('countdown');
    const startTimeInput = document.getElementById('start-time');

    // Parse the formatted start time value from the input element as UTC time
    const startTimeUTC = new Date(startTimeInput.value);

    // Convert UTC start time to user's local time
    const startTimeLocal = new Date(startTimeUTC);
    const offset = startTimeLocal.getTimezoneOffset();
    startTimeLocal.setMinutes(startTimeLocal.getMinutes() - offset);

    // Calculate end time (start time + 5 minutes)
    const endTime = new Date(startTimeLocal);
    endTime.setMinutes(endTime.getMinutes() + 5);

    function updateCountdown() {
        const now = new Date();
        const timeLeft = endTime - now;

        if (timeLeft <= 0) {
            // If time is up, clear the interval and update the display
            clearInterval(interval);
            timeRemainingElement.innerHTML = 'Time is up!';
            return;
        }

        const seconds = Math.floor(timeLeft / 1000);
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;

        timeRemainingElement.innerHTML = `${hours}h ${minutes}m ${remainingSeconds}s`;
    }

    // Update every second and store the interval reference
    const interval = setInterval(updateCountdown, 1000);

    // Initial update
    updateCountdown();
});
