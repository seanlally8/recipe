// Main JavaScript file


// Allow user to take more than one picture
document.addEventListener('DOMContentLoaded', () => {


	// When the user clicks next, replace existing form with a file-upload element
	document.querySelector('#next-button').onclick = () => {
		
		// We will collect the title here instead of finding it with OCR
		var title  =  document.querySelector('#recipe-title').value;

		// This is where we'll store the files before submitting via post to server
		let fileList = [];

		// Here's where we actually update the html
		document.querySelector('#scan-form').innerHTML =  '<label for="file-upload" class="btn btn-dark">Browse</label> \
		<input type="file"  accept="image/*" id="file-upload" multiple name="image" style="display: none"> \
		<button class="btn btn-dark" id="upload-button">Upload</button>';

		// We'll use this to access the files selected by user
		let fileUpload = document.querySelector('#file-upload');

		// When a new file is opened, add it to fileList in preparation for submission.
		// This allows us to hit the browse button more than once and still retain all the
		// selected files.
		fileUpload.onchange = () => {

			// Add selected files to file list
			for (let i = 0; i < fileUpload.files.length; i++) {
				fileList.push(fileUpload.files[i]);
			}

			// DEBUGGING
			console.log(title);
			for (let i = 0; i < fileList.length; i++) {
				console.log(fileList[i]);
			}

			// We'll need to listen for the upload button being clicked 
			let fileSubmit = document.querySelector('#upload-button')

			// If upload button is clicked, send the title and file(s) to the server
			fileSubmit.onclick = () => {
				
				// Create FormData object containing items to be sent to server
				const formData = new FormData();
				
				// Add items to FormData object: the recipe's title and the images
				formData.append('title', title);

				for (let i = 0; i < fileList.length; i++) {
					formData.append(`photos_${i}`, fileList[i]);
				}

				fetch('/', {
					method: 'POST',
					body: formData
				})

				.then(response => response.json())

				.then(result => {
					console.log('Success:', result);
				})

				.catch(error => {
					console.error('Error:', error);
				});
			};
		};
	};
});

