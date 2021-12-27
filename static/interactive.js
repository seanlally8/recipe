// Main JavaScript file


// Allow user to take more than one picture
document.addEventListener('DOMContentLoaded', () => {


	// When the user clicks next, replace existing form with a file-upload element
	document.querySelector('#nextbutton').onclick = () => {
		
		// We will collect the title here instead of finding it with OCR
		let title  =  document.querySelector('#recipetitle').value;

		// This is where we'll store the files before submitting via post to app.py
		let fileList = [];

		// Here's where we actually update the html
		document.querySelector('#scan-form').innerHTML =  '<label for="file-upload" class="btn btn-dark">Browse</label> \
		<input type="file"  accept="image/*" id="file-upload" multiple name="image" style="display: none"> \
		<input type="submit" class="btn btn-dark" value="Upload">';

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
		};
	};
	
});

