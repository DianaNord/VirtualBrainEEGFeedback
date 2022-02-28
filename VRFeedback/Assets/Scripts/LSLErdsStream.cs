using UnityEngine;
using LSL;
using System;
using System.Collections;


public class LSLErdsStream : MonoBehaviour
{
    string lslStreamName;
    liblsl.StreamInlet streamInlet;
    liblsl.StreamInfo[] streamInfos;
    float[] sample;
    int channelCount = 0;

    void Start()
    {
        lslStreamName = ScenarioController.instance.LSLStreamNameFbErds;
    }


    public bool Initialize()
    {
        bool initialized = false;

        if (streamInlet != null)
        {
            Debug.Log("INFO: ERDS stream is already resolved!");
            return initialized;
        }
        if (string.IsNullOrEmpty(lslStreamName))
		{
			Debug.Log("ERROR: No name for the LSL ERDS stream was provided!");
			return initialized;
		}
                
        try
        {
            streamInfos = liblsl.resolve_stream("name", lslStreamName, 1, 10.0f);
        }
        catch (TimeoutException)
        {
            Debug.Log("ERROR: Timeout resolving LSL ERDS stream!");
        }

        if (streamInfos.Length == 0 || streamInfos[0] == null)
            Debug.Log("ERROR: LSL ERDS stream could not be resolved!");
        else
        {
            streamInlet = new liblsl.StreamInlet(streamInfos[0]);
            channelCount = streamInlet.info().channel_count();
            streamInlet.open_stream();
            initialized = true;
        }

        Debug.Log("Finish Initialize ERDS");

        return initialized;
    }

    void Update()
    {
        if (streamInlet == null)
            return;

        sample = new float[channelCount];
        double lastTimeStamp = streamInlet.pull_sample(sample, 0.0f);
        if (lastTimeStamp != 0.0)
        {
            Process(sample, lastTimeStamp);
            while ((lastTimeStamp = streamInlet.pull_sample(sample, 0.0f)) != 0)
            {
                Process(sample, lastTimeStamp);
            }
        } 
    }

    void Process(float[] newSample, double timeStamp)
    {
        EventManager.instance.OnTriggerUpdateERDS(newSample);
    }
}