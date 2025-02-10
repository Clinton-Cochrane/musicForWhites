chrome.runtime.onMessage.addListener((message,sender,sendResponse) => {
    if( message.mute) {
        let [start, end] = message.mute;
        muteAudio(start,end);
    }
});

function muteAudio(start, end){
    let video = document.querySelector("video, audio");
    if(video) {
        video.muted = true;
        setTimeout(() => {
            video.muted = false;
        }, (end - start) * 1000)
    }
}