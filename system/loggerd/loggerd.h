#pragma once

#include <vector>
#include <string>
#include <cctype>

#include "cereal/messaging/messaging.h"
#include "cereal/services.h"
#include "msgq/visionipc/visionipc_client.h"
#include "system/hardware/hw.h"
#include "common/params.h"
#include "common/swaglog.h"
#include "common/util.h"

#include "system/loggerd/logger.h"

constexpr int MAIN_FPS = 20;
const int MAIN_BITRATE = 1e7;
const int LIVESTREAM_BITRATE = 1e6;

#define NO_CAMERA_PATIENCE 500  // fall back to time-based rotation if all cameras are dead

#define INIT_ENCODE_FUNCTIONS(encode_type)                                \
  .get_encode_data_func = &cereal::Event::Reader::get##encode_type##Data, \
  .set_encode_idx_func = &cereal::Event::Builder::set##encode_type##Idx,  \
  .init_encode_data_func = &cereal::Event::Builder::init##encode_type##Data

const bool LOGGERD_TEST = getenv("LOGGERD_TEST");
const int SEGMENT_LENGTH = LOGGERD_TEST ? atoi(getenv("LOGGERD_SEGMENT_LENGTH")) : 60;

constexpr char PRESERVE_ATTR_NAME[] = "user.preserve";
constexpr char PRESERVE_ATTR_VALUE = '1';
class EncoderInfo {
public:
  const char *publish_name;
  const char *thumbnail_name = NULL;
  const char *filename = NULL;
  bool record = true;
  int frame_width = -1;
  int frame_height = -1;
  int fps = MAIN_FPS;
  int bitrate = MAIN_BITRATE;
  cereal::EncodeIndex::Type encode_type = cereal::EncodeIndex::Type::FULL_H_E_V_C;
  ::cereal::EncodeData::Reader (cereal::Event::Reader::*get_encode_data_func)() const;
  void (cereal::Event::Builder::*set_encode_idx_func)(::cereal::EncodeIndex::Reader);
  cereal::EncodeData::Builder (cereal::Event::Builder::*init_encode_data_func)();
};

class LogCameraInfo {
public:
  const char *thread_name;
  int fps = MAIN_FPS;
  VisionStreamType stream_type;
  std::vector<EncoderInfo> encoder_infos;
};

const EncoderInfo main_road_encoder_info = {
  .publish_name = "roadEncodeData",
  .filename = "fcamera.hevc",
  INIT_ENCODE_FUNCTIONS(RoadEncode),
};

const EncoderInfo main_wide_road_encoder_info = {
  .publish_name = "wideRoadEncodeData",
  .filename = "ecamera.hevc",
  INIT_ENCODE_FUNCTIONS(WideRoadEncode),
};

const EncoderInfo main_driver_encoder_info = {
  .publish_name = "driverEncodeData",
  .filename = "dcamera.hevc",
  .record = Params().getBool("RecordFront"),
  INIT_ENCODE_FUNCTIONS(DriverEncode),
};

const EncoderInfo stream_road_encoder_info = {
  .publish_name = "livestreamRoadEncodeData",
  //.thumbnail_name = "thumbnail",
  .encode_type = cereal::EncodeIndex::Type::QCAMERA_H264,
  .record = false,
  .bitrate = LIVESTREAM_BITRATE,
  INIT_ENCODE_FUNCTIONS(LivestreamRoadEncode),
};

const EncoderInfo stream_wide_road_encoder_info = {
  .publish_name = "livestreamWideRoadEncodeData",
  .encode_type = cereal::EncodeIndex::Type::QCAMERA_H264,
  .record = false,
  .bitrate = LIVESTREAM_BITRATE,
  INIT_ENCODE_FUNCTIONS(LivestreamWideRoadEncode),
};

const EncoderInfo stream_driver_encoder_info = {
  .publish_name = "livestreamDriverEncodeData",
  .encode_type = cereal::EncodeIndex::Type::QCAMERA_H264,
  .record = false,
  .bitrate = LIVESTREAM_BITRATE,
  INIT_ENCODE_FUNCTIONS(LivestreamDriverEncode),
};

inline const char* generate_publish_name(const char* name) {
  static std::string result;
  result = std::string(1, std::tolower(name[0])) + std::string(name).substr(1) + "EncodeData";
  printf("publish_name: %s\n", result.c_str());
  return result.c_str();
}

#define DEFINE_ENCODER_INFO(filename_prefix, encoder_bitrate, width, height, encode_func) \
  const EncoderInfo filename_prefix##_encoder_info = { \
    .filename = #filename_prefix ".ts", \
    .bitrate = encoder_bitrate, \
    .encode_type = cereal::EncodeIndex::Type::QCAMERA_H264, \
    .frame_width = width, \
    .frame_height = height, \
    .publish_name = generate_publish_name(#encode_func), \
    INIT_ENCODE_FUNCTIONS(encode_func##Encode), \
  };

// QCAM (526x330) original @ 256kbps

// OS04C10 (1344x760)
// AR/OX (1928x1208)

const int QCAM_BITRATE = 256000;
const int HIGH_BITRATE = 1024 * 1024;  // 8 MB per minute
const int HIGHER_BITRATE = 1.25 * 1024 * 1024;  // 10 MB per minute
const int VERY_HIGH_BITRATE = 2 * 1024 * 1024;  // 16 MB per minute
const int EXTREME_BITRATE = 4 * 1024 * 1024;  // 32 MB per minute

DEFINE_ENCODER_INFO(qcamera, HIGH_BITRATE, 1148, 720, QRoad)
DEFINE_ENCODER_INFO(qcamera_boost, HIGHER_BITRATE, 1148, 720, Debug0)
// DEFINE_ENCODER_INFO(qcamera_720_vh, VERY_HIGH_BITRATE, 1148, 720, Debug0)
// DEFINE_ENCODER_INFO(qcamera_720_ex, EXTREME_BITRATE, 1148, 720, Debug1)
// DEFINE_ENCODER_INFO(qcamera_902_vh, VERY_HIGH_BITRATE, 1440, 902, Debug2)
// DEFINE_ENCODER_INFO(qcamera_902_ex, EXTREME_BITRATE, 1440, 902, Debug3)
// DEFINE_ENCODER_INFO(qcamera_1208_ex, EXTREME_BITRATE, 1928, 1208, Debug4)
// DEFINE_ENCODER_INFO(qcamera_1208, 2 * EXTREME_BITRATE, 1928, 1208, Debug5)

// DEFINE_ENCODER_INFO("qcamera", QRoad, QCAM_BITRATE, 526, 330)
// DEFINE_ENCODER_INFO("qcamera_330_1m", Debug0, HIGH_BITRATE, 526, 330)
// DEFINE_ENCODER_INFO("qcamera_720_1m", Debug1, HIGH_BITRATE, 1148, 720)
// DEFINE_ENCODER_INFO("qcamera_902_1m", Debug2, HIGH_BITRATE, 1440, 902)
// DEFINE_ENCODER_INFO("qcamera_902_2m", Debug3, VERY_HIGH_BITRATE, 1440, 902)
// DEFINE_ENCODER_INFO("qcamera_902_4m", Debug4, EXTREME_BITRATE, 1440, 902)

const LogCameraInfo road_camera_info{
  .thread_name = "road_cam_encoder",
  .stream_type = VISION_STREAM_ROAD,
  .encoder_infos = {
    main_road_encoder_info,
    qcamera_encoder_info,
    qcamera_boost_encoder_info,
    // qcamera_720_vh_encoder_info,
    // qcamera_720_ex_encoder_info,
    // qcamera_902_vh_encoder_info,
    // qcamera_902_ex_encoder_info,
    // qcamera_1208_ex_encoder_info,
  },
};

const LogCameraInfo wide_road_camera_info{
  .thread_name = "wide_road_cam_encoder",
  .stream_type = VISION_STREAM_WIDE_ROAD,
  .encoder_infos = {main_wide_road_encoder_info}
};

const LogCameraInfo driver_camera_info{
  .thread_name = "driver_cam_encoder",
  .stream_type = VISION_STREAM_DRIVER,
  .encoder_infos = {main_driver_encoder_info}
};

const LogCameraInfo stream_road_camera_info{
  .thread_name = "road_cam_encoder",
  .stream_type = VISION_STREAM_ROAD,
  .encoder_infos = {stream_road_encoder_info}
};

const LogCameraInfo stream_wide_road_camera_info{
  .thread_name = "wide_road_cam_encoder",
  .stream_type = VISION_STREAM_WIDE_ROAD,
  .encoder_infos = {stream_wide_road_encoder_info}
};

const LogCameraInfo stream_driver_camera_info{
  .thread_name = "driver_cam_encoder",
  .stream_type = VISION_STREAM_DRIVER,
  .encoder_infos = {stream_driver_encoder_info}
};

const LogCameraInfo cameras_logged[] = {road_camera_info, wide_road_camera_info, driver_camera_info};
const LogCameraInfo stream_cameras_logged[] = {stream_road_camera_info, stream_wide_road_camera_info, stream_driver_camera_info};
