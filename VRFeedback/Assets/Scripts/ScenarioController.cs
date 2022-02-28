using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

public class ScenarioController : MonoBehaviour
{
    public static ScenarioController instance;
    public int numberRun = 1; 
	public bool showFeedback = true;
	public bool startSession = false;

	public enum AllConditions
	{
		LEFT_HAND=0,
		RIGHT_HAND
	};

	// ------------- private variables -------------
	const string PathConfig = "Assets/../../bci-config.json";
    const string Path = "Assets/Resources/MI_run_";
	int round = -1;
	uint condition;
	float[] timeBreak = new float[2];

	WaitForSecondsRealtime waitSecondsRef;
	WaitForSecondsRealtime waitSecondsCue;
	WaitForSecondsRealtime waitSecondsFb;
	private string lslStreamNameMarker;
	private string lslStreamIdMarker;
	private string lslStreamNameFbCl;
	private string lslStreamNameFbErds;
	System.Random random = new System.Random();

	Dictionary<string, uint> ConditionStrToInt = new Dictionary<string, uint> 
	{
		{ "l", (uint)AllConditions.LEFT_HAND },
		{ "r", (uint)AllConditions.RIGHT_HAND }
	};

	Dictionary<uint, string> ConditionIntToStr = new Dictionary<uint, string> 
	{
		{ (uint)AllConditions.LEFT_HAND, "l"},
		{ (uint)AllConditions.RIGHT_HAND, "r"}
	};

	// ------------- internal variables -------------
	internal List<string> blockSequence;
	internal LSLFeedbackStream feedbackStream;
	internal LSLErdsStream erdsStream;

	public string LSLStreamNameMarker{get{return lslStreamNameMarker;} set{lslStreamNameMarker = value;}}
	public string LSLStreamIdMarker{get{return lslStreamIdMarker;} set{lslStreamIdMarker = value;}}
	public string LSLStreamNameFbCl{get{return lslStreamNameFbCl;} set{lslStreamNameFbCl = value;}}
	public string LSLStreamNameFbErds{get{return lslStreamNameFbErds;} set{lslStreamNameFbErds = value;}}


	void Awake()
	{
        if (instance == null)
            instance = this;
        else
            Destroy(this);

        LoadConfiguration();
	}

	void LoadConfiguration()
	{
		blockSequence = new List<String>(File.ReadAllLines(Path+numberRun+".txt"));

		string jsonString = File.ReadAllText(PathConfig);
		var obj = (JObject)JsonConvert.DeserializeObject(jsonString);

		waitSecondsRef = new WaitForSecondsRealtime(obj["general-settings"]["timing"]["duration-ref"].Value<float>());
		waitSecondsCue = new WaitForSecondsRealtime(obj["general-settings"]["timing"]["duration-cue"].Value<float>());
		waitSecondsFb = new WaitForSecondsRealtime(obj["general-settings"]["timing"]["duration-task"].Value<float>());

		JArray timeB = obj["general-settings"]["timing"]["duration-break"].Value<JArray>();
		timeBreak[0] = timeB[0].Value<float>();
		timeBreak[1] = timeB[1].Value<float>();

		LSLStreamNameFbCl = obj["general-settings"]["lsl-streams"]["fb-lda"]["name"].Value<string>();
		LSLStreamNameMarker = obj["general-settings"]["lsl-streams"]["marker"]["name"].Value<string>();
		LSLStreamIdMarker = obj["general-settings"]["lsl-streams"]["marker"]["id"].Value<string>();
		LSLStreamNameFbErds = obj["general-settings"]["lsl-streams"]["fb-erds"]["name"].Value<string>();
		
	}
	
    IEnumerator Start()
    {
		if (showFeedback)
		{
			feedbackStream = gameObject.GetComponent<LSLFeedbackStream>();
			erdsStream = gameObject.GetComponent<LSLErdsStream>();
		}

		Debug.Log("INFO: Wait until session is started by user...");

		yield return new WaitUntil(() => startSession == true);

		StartBlock();
	}

    public void StartBlock()
    {
		if (showFeedback)
		{
			bool fb_initialized = feedbackStream.Initialize() && erdsStream.Initialize();

			if (!fb_initialized)
				QuitGame();
		} 

		round = 0;
		UpdateCondition();
		EventManager.instance.OnTriggerSessionStarted();
		StartCoroutine(StartTrial());
    }

	public IEnumerator StartTrial()
    {
		yield return new WaitForSecondsRealtime(NextFloat(timeBreak));

		EventManager.instance.OnTriggerTrialStarted(ConditionIntToStr[condition]);

        EventManager.instance.OnTriggerReference();
        yield return waitSecondsRef;

        EventManager.instance.OnTriggerCue(condition);
        yield return waitSecondsCue;

        EventManager.instance.OnTriggerFeedback(condition);
		yield return waitSecondsFb;

		EventManager.instance.OnTriggerTrialEnd();

		EndTrial();		
    }
	
	void EndTrial()
    {		
        round = round + 1;
        if (round >= blockSequence.Count)
            BlockFinished();
        else
        {
            UpdateCondition();
			StartCoroutine(StartTrial());
        }        
    }

	void UpdateCondition()
	{
		string[] str = blockSequence[round].Split('_');
		condition = ConditionStrToInt[str[str.Length-1]];
		if (showFeedback)
			feedbackStream.CurrentCondition = condition;
	}

	float NextFloat(float[] range)
	{
		double val = (random.NextDouble() * (range[1] - range[0]) + range[0]);
		return (float)val;
	}
	
	void BlockFinished() 
    {
		startSession = false;
		EventManager.instance.OnTriggerSessionFinished();
    }

	public void QuitGame()
    {
		#if UNITY_EDITOR
			UnityEditor.EditorApplication.isPlaying = false;
		#else
			Application.Quit();
		#endif
    }

}
