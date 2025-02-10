import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:audioplayer/audioplayers.dart';

void main (){
    runApp(const MyApp());
}

class MusicForWhites extends StatelessWidget {
    const MusicForWhites({super.key});

    @override
    Widget build(BuildContext context){
        return MaterialApp(
            title: 'Music For Whites',
            home: MusicFilterScreen(),
        );
    }
}

class MusicFilterScreen extends StatefulWidget {
    @override
    _MusicFilterScreenState createState() => _MusicFilterScreenState();
}

class _MusicFilterScreenState extends State<MusicFilterScreen> {
    late WebSocketChannel channel;
    final AudioPlayer _audioPlayer = AudioPlayer();
    bool isMuted = false;

    @override
    void initState(){
        super.initState();
        channel = WebSocketChannel.connect(Uri.parse("ws://theserveraddress:8000"))
        listenForMuteCommands();
    }

    void listenForMuteCommands(){
        channel.steam.listen((message){
            if(message.contains("MUTE")){
                setState((){ 
                    isMuted = true;
                });

                _audioPlayer.setVolume(0);
                Future.delayed(Duration(seconds: 2), () {
                    setState(() {
                        isMuted = false;
                    });
                    _audioPlayer.setVolume(1);
                });
            };
        });
    }

    void startMusic() async {
        await _audioPlayer.play(UrlSource("https://song.mp3"));
    }

    @override
    Widget build (BuildContext context){
        return Scaffold(
            appBar: AppBar(title: Text("Music Censorship")),
            body: Center(
                child: Column(
                    mainAxisAlignment: mainAxisAlignment.center,
                    children: [
                        Text(isMuted? "Muted...": "Playing music"),
                        ElevatedButton(onPressed: startMusic, child: Text("Start Music")),
                    ],
                ),
            ),
        );
    }

    @override
    void dispose(){
        channel.sink.close();
        _audioPlayer.dispose()
        super.dispose()
    }
}