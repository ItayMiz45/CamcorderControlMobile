import 'dart:async';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'action_IDs.dart';

const DB_NAME = "database.txt";


Future<String> get _localPath async {
  final directory = await getApplicationDocumentsDirectory();
  return directory.path;
}

Future<File> get _localFile async {
  final path = await _localPath;
  return File('$path/$DB_NAME');
}

void writeAllDB(int act1, int act2, int act3) {
  _localFile.then((file) {
    file.writeAsStringSync("$act1$act2$act3");
  });
}

Future<String> readAllDB() async {
  final file = await _localFile;

  return file.readAsStringSync();
}

void initDB() {
  _localFile.then((file) {
    if(!file.existsSync())
      writeAllDB(ACTION_VOL_UP, ACTION_VOL_DOWN, ACTION_NONE);
  });
}