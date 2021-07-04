// @dart=2.9

import 'dart:async';
import 'dart:io';

// ignore: import_of_legacy_library_into_null_safe
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:schoolproject/gesture_action.dart';
import 'websocket_manager.dart';
import 'package:flutter_restart/flutter_restart.dart';
import 'plaintext_db_manager.dart';
import 'gesture_action.dart';
import 'action_IDs.dart';


Future<void> main() async {
  // Ensure that plugin services are initialized so that `availableCameras()`
  // can be called before `runApp()`
  WidgetsFlutterBinding.ensureInitialized();

  // Obtain a list of the available cameras on the device.
  final cameras = await availableCameras();

  // Get front facing camera from the list of available cameras.
  final camToUse = cameras.length > 1 ? cameras[1] : cameras[0];

  initDB();

  writeAllDB(ACTION_VOL_UP, ACTION_VOL_DOWN, ACTION_NONE);
  String actionIDs = await readAllDB();
  print("THis is what i read:");
  print(actionIDs);

  GestureAction.init(actionIDs);

  runApp(
    MaterialApp(
      theme: ThemeData.dark(),
      home: MainPage(
        // Pass the appropriate camera to the TakePictureScreen widget.
        camera: camToUse, key: Key(""),
      ),
    ),
  );
}

// A screen that allows users to take a picture using a given camera.
class MainPage extends StatefulWidget {
  final CameraDescription camera;

  const MainPage({
    Key key,
    this.camera,
  }) : super(key: key);

  @override
  _MainPageState createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  CameraController _controller;
  CameraImage _savedImage;
  Future<void> _initializeControllerFuture;
  WebSocketManager _webSocketManager;
  String _prediction = "0";

  @override
  void initState() {
    super.initState();

    // Create Web Socket
    _webSocketManager = WebSocketManager();

    // To display the current output from the Camera,
    // create a CameraController.
    _controller = CameraController(
      // Get a specific camera from the list of available cameras.
      widget.camera,
      // Define the resolution to use.
      ResolutionPreset.low,  // low: 320x240 / medium: 720x480
    );

    // Next, initialize the controller. This returns a Future.
    _initializeControllerFuture = _controller.initialize();

    _initializeControllerFuture.then((_) async{
      // Start ImageStream
      await _controller.startImageStream((CameraImage image) =>
          _processCameraImage(image));
    });

    // Send image and receive prediction every x milliseconds
    Timer.periodic(Duration(milliseconds: 75), (timer) async {
      _webSocketManager.send(_savedImage.planes[0].bytes);
      _prediction = await _webSocketManager.getData();
      GestureAction.performAction(int.parse(_prediction));
    });
  }

  void _processCameraImage(CameraImage image) async {
    setState(() {
      _savedImage = image;
    });
  }

  @override
  void dispose() {
    // Dispose of the controller when the widget is disposed.
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Take a picture')),
      // Wait until the controller is initialized before displaying the
      // camera preview. Use a FutureBuilder to display a loading spinner
      // until the controller has finished initializing.
      body: Column(
        children: [
          FutureBuilder<void>(
            future: _initializeControllerFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.done) {
                // If the Future is complete, display the preview.
             return CameraPreview(_controller);
  //               return AspectRatio(
  //                 aspectRatio: _controller.value.aspectRatio,
  //                 child: CameraPreview(_controller),
  //               );
              } else {
                // Otherwise, display a loading indicator.
                return Center(child: CircularProgressIndicator());
              }
            },
          ),
          Text(_prediction),
        ]
      ),

      floatingActionButton: FloatingActionButton(
        child: Icon(Icons.refresh_outlined),
        onPressed: () async {
          FlutterRestart.restartApp();
        },
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
    );
  }
}


// // A widget that displays the picture taken by the user.
// class DisplayPictureScreen extends StatelessWidget {
//   final String imagePath;
//
//   const DisplayPictureScreen({Key key, this.imagePath}) : super(key: key);
//
//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(title: Text('Display the Picture')),
//       // The image is stored as a file on the device. Use the `Image.file`
//       // constructor with the given path to display the image.
//       body: Image.file(File(imagePath)),
//     );
//   }
// }