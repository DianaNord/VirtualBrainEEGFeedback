using UnityEngine;
using LSL;
using System;

public class LSLMarkerStream : MonoBehaviour
{
    string lslStreamName;
    string lslSourceId;
    const int LslChannelCount = 1;
    const double NominalSrate = liblsl.IRREGULAR_RATE;
    const liblsl.channel_format_t LslChannelFormat = liblsl.channel_format_t.cf_string;

    liblsl.StreamInfo lslStreamInfo;
    liblsl.StreamOutlet lslOutlet;
    string[] sample;

    void Start()
    {
        lslStreamName = ScenarioController.instance.LSLStreamNameMarker;
        lslSourceId = ScenarioController.instance.LSLStreamIdMarker;
        if (!Initialize())
            ScenarioController.instance.QuitGame();
    }

    public bool Initialize()
    {
		if (string.IsNullOrEmpty(lslStreamName))
		{
			Debug.Log("ERROR: No name for the LSL marker stream was provided!");
			return false;
		}
		
        sample = new string[LslChannelCount];

        lslStreamInfo = new liblsl.StreamInfo(
                                    lslStreamName,
                                    "Marker",
                                    LslChannelCount,
                                    NominalSrate,
                                    LslChannelFormat,
                                    lslSourceId);

        lslOutlet = new liblsl.StreamOutlet(lslStreamInfo);
		return true;
    }

    public void Write(string marker)
    {
		if (lslOutlet == null)
			return;
        sample[0] = marker;
        lslOutlet.push_sample(sample, liblsl.local_clock());
        print(marker);
    }
}