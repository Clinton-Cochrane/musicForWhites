let socket = new WebSocket("ws://localhost:8000");

socket.onmessage = (event) => {
    let data = JSON.parse(event.data);
    if(data.mute){
        let [start, end] = data.mute;
        chrome.tabs.query({active:true, currentWindow: true}, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, {mute:[start, end]});
        })
    }
}