function __log(e, data) {
  log.innerHTML += "\n" + e + " " + (data || '');
}
var audio_context;
var recorder;
function startUserMedia(stream) {
  var input = audio_context.createMediaStreamSource(stream);
  __log('Media stream created.');
  // Uncomment if you want the audio to feedback directly
  // input.connect(audio_context.destination);
  // __log('Input connected to audio context destination.');
  
  recorder = new Recorder(input);
  __log('Recorder initialised.');
}
function startRecording(button) {
  recorder && recorder.record();
  button.disabled = true;
  button.nextElementSibling.disabled = false;
  __log('Recording...');
}
function stopRecording(button) {
  recorder && recorder.stop();
  button.disabled = true;
  button.previousElementSibling.disabled = false;
  __log('Stopped recording.');
  
  // create WAV download link using audio data blob
  createDownloadLink();
  
  recorder.clear();
}
function createDownloadLink() {
  recorder && recorder.exportWAV(function(blob) {
    var url = URL.createObjectURL(blob);
    var li = document.createElement('li');
    var au = document.createElement('audio');
    var hf = document.createElement('a');
    
    au.controls = true;
    au.src = url;
    hf.href = url;
    hf.download = new Date().toUTCString() + '.wav';
    hf.innerHTML = hf.download;
    li.appendChild(au);
    li.appendChild(hf);
    recordingslist.appendChild(li);

    var form = new FormData();
    var reqID = $( '#request-id' ).html();    

    form.append('file', blob, hf.download);
    
    $('#submit-audio').click(function() {
      var myTranscript = $( '#final_span' ).html();
      
      form.append('title', $('#recording-title').val());
      form.append('desc', $('#recording-desc').val());
      form.append('transcript', myTranscript);
      alert(myTranscript);
      alert('Submitting!');
      $.ajax({
        type: 'POST',
        url: '/request/' + reqID,
        data: form,
        cache: false,
        processData: false,
        contentType: false,
      }).done(function(data) {
        console.log(data);
      });
    });

  });
}
window.onload = function init() {
  try {
    // webkit shim
    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia;
    window.URL = window.URL || window.webkitURL;
    
    audio_context = new AudioContext;
    __log('Audio context set up.');
    __log('navigator.getUserMedia ' + (navigator.getUserMedia ? 'available.' : 'not present!'));
  } catch (e) {
    alert('No web audio support in this browser!');
  }
  
  navigator.getUserMedia({audio: true}, startUserMedia, function(e) {
    __log('No live audio input: ' + e);
  });
};