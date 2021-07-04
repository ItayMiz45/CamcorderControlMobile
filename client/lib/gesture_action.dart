import 'dart:async';
import 'package:volume_control/volume_control.dart';
import 'action_IDs.dart';

class GestureAction {

  // key: gestureID, value: action function
  static Map<int, Function> _gestureActionMap = Map<int, Function>();
  static bool _inTimeout = false;

  /*
  Initialize the gesture-action map with user settings stored in database (actionIDs)
   */
  static void init(String actionIDs) {
    for(int i = 0; i < actionIDs.length; i++) {
      switch (int.parse(actionIDs[i])) {
        case ACTION_VOL_UP:
          _gestureActionMap[i+1] = _volumeUp;
          break;
        case ACTION_VOL_DOWN:
          _gestureActionMap[i+1]  = _volumeDown;
      }
    }

    print(_gestureActionMap);
  }

  static void performAction(int gestureID) {
    var func = _gestureActionMap[gestureID];
    if (!_inTimeout && func != null) {
      func();

      _inTimeout = true;
      Timer(Duration(milliseconds: 750), () => _inTimeout = false);
    }
  }

  static void _volumeUp({double d: 0.1}) {
    VolumeControl.volume.then((currVol) {
      VolumeControl.setVolume(currVol + d);
      print(currVol);
    });
  }

  static void _volumeDown({double d: 0.1}) {
    VolumeControl.volume.then((currVol) {
      VolumeControl.setVolume(currVol - d);
      print(currVol);
    });
  }
}