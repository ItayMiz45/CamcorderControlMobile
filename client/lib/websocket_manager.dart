// @dart=2.9

import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';


const HOST = "192.168.1.32";
const PORT = 34567;


class WebSocketManager {
  String host;
  int port;
  WebSocketChannel channel;
  Stream _broadcastStream;

  WebSocketManager({this.host=HOST, this.port=PORT}) {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://$HOST:$PORT'),
    );

    _broadcastStream = channel.stream.asBroadcastStream();
    channel.sink.add("Hello Server!");
    getData();
  }


  Future<String> getData() async {
    return await _broadcastStream.first;
  }

  void send(var data) {
    channel.sink.add(data);
  }
}