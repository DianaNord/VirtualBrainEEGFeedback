using UnityEngine;
using LSL;
using System;

/// <summary>
/// Creates a LSL stream and writes the markers to the stream outlet.
/// </summary>
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

    /// <summary>
    /// Reads the name and id of the LSL stream from the ScenarioController instance.
    /// Is called on the frame when a script is enabled just before any of the Update methods are called the first time.
    /// </summary>
    void Start()
    {
        lslStreamName = ScenarioController.instance.LSLStreamNameMarker;
        lslSourceId = ScenarioController.instance.LSLStreamIdMarker;
        if (!Initialize())
            ScenarioController.instance.QuitGame();
    }

    /// <summary>
    /// Creates the stream outlet.
    /// </summary>
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

    /// <summary>
    /// Write the marker to the stream outlet.
    /// </summary>
    public void Write(string marker)
    {
		if (lslOutlet == null)
			return;
        sample[0] = marker;
        lslOutlet.push_sample(sample, liblsl.local_clock());
        print(marker);
    }
}