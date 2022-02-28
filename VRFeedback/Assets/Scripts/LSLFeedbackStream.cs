using UnityEngine;
using LSL;
using System;
using System.Collections;

public class LSLFeedbackStream : MonoBehaviour
{
    string lslStreamName;
    liblsl.StreamInfo[] streamInfos;
    liblsl.StreamInlet streamInlet;
    float[] sample;
    int channelCount = 0;

    private uint currentCondition;	
	public uint CurrentCondition{get{return currentCondition;} set{currentCondition = value;}}

    void Start()
    {
        lslStreamName = ScenarioController.instance.LSLStreamNameFbCl;
    }

    public bool Initialize()
    {
        Debug.Log("Initialize Feedback");
        bool initialized = false;

        if (streamInlet != null)
        {
            Debug.Log("INFO: Feedback stream is already resolved!");
            return initialized;
        }
        if (string.IsNullOrEmpty(lslStreamName))
		{
			Debug.Log("ERROR: No name for the LSL feedback stream was provided!");
			return initialized;
		}
        
        try
        {
            streamInfos = liblsl.resolve_stream("name", lslStreamName, 1, 10.0f);
        }
        catch (TimeoutException)
        {
            Debug.Log("ERROR: Timeout resolving LSL feedback stream!");
        }

        if (streamInfos.Length == 0 || streamInfos[0] == null)
            Debug.Log("ERROR: LSL feedback stream could not be resolved!");
        else
        {
            streamInlet = new liblsl.StreamInlet(streamInfos[0]);
            channelCount = streamInlet.info().channel_count();
            streamInlet.open_stream();
            initialized = true;
        }

        Debug.Log("Finish Initialize Feedback");

        return initialized;
    }

    void Update()
    {
        if (streamInlet == null)
            return;

        sample = new float[channelCount];  // FIXME why "new", stack also ok?
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
        bool is_classifier_correctly = (uint) newSample[0] == currentCondition;
        
        EventManager.instance.OnTriggerUpdateGlow(newSample[1], is_classifier_correctly);
    }

}