let debounceTimeout;
function updateThresholdValue(value, imageFilename) {
    document.getElementById('thresholdValue').textContent = value;
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
        fetch('/update_threshold', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                threshold: value,
                image_filename: imageFilename
            })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('combinedImage').src = '/' + data.combined_image + '?' + new Date().getTime();
        });
    }, 200); // Adjust debounce timeout as needed
}
