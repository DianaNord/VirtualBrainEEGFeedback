using UnityEngine;

public class ObjectsController : MonoBehaviour
{
    public GameObject fixationCross;
    public GameObject arrowLeft;
	public GameObject arrowRight;
	public GameObject brain;
    public GameObject glow;

    internal LSLFeedbackStream feedbackStream;
    internal LSLMarkerStream markerStream;
    internal TextureColorController textureController;

    void Start()
    {
		feedbackStream = gameObject.GetComponent<LSLFeedbackStream>();
        markerStream = gameObject.GetComponent<LSLMarkerStream>();
        textureController = gameObject.GetComponent<TextureColorController>();

        EventManager.instance.TriggerSessionStarted += OnSessionStarted;
        EventManager.instance.TriggerSessionFinished += OnSessionFinished;
        EventManager.instance.TriggerTrialStarted += OnTrialStarted;
        EventManager.instance.TriggerReference += OnReference;
        EventManager.instance.TriggerCue += OnCue;
        EventManager.instance.TriggerFeedback += OnFeedback;
        EventManager.instance.TriggerTrialEnd += OnTrialEnd;
        EventManager.instance.TriggerResetObjects += OnResetObjects;
        EventManager.instance.TriggerUpdateGlow += OnUpdateGlow;
        EventManager.instance.TriggerUpdateERDS += OnUpdateERDS;

        OnResetObjects();
    }

    void OnSessionStarted()
    {
        markerStream.Write("Session_Start");
    }

    void OnSessionFinished()
    {
        markerStream.Write("Session_End");
    }

    void OnTrialStarted(string condition)
    {
        markerStream.Write("Start_of_Trial_" + condition);
    }

    void OnReference()
    {
        markerStream.Write("Reference");
        fixationCross.SetActive(true);
    }

    void OnCue(uint condition)
    {
        markerStream.Write("Cue");
        if (condition == (uint)ScenarioController.AllConditions.LEFT_HAND)
            arrowLeft.SetActive(true);
        else if (condition == (uint)ScenarioController.AllConditions.RIGHT_HAND)
            arrowRight.SetActive(true);
    }

    void OnFeedback(uint condition)
    {
        if (!ScenarioController.instance.showFeedback)
            return;

        fixationCross.SetActive(false);

        markerStream.Write("Feedback");

        brain.SetActive(true);
        glow.SetActive(true);	

    }

    void OnTrialEnd()
    {
        markerStream.Write("End_of_Trial");
        
        OnResetObjects();
        if (ScenarioController.instance.showFeedback)
        {
            textureController.ResetTexture();  // TODO check (is also in onresetobjects)
        }

    }

    public void OnResetObjects()
	{
        fixationCross.SetActive(false);
		arrowLeft.SetActive(false);
		arrowRight.SetActive(false);
		brain.SetActive(false);
        glow.SetActive(false);	

        textureController.ResetTexture();
	}

    void OnUpdateGlow(float distance, bool is_correct)
    {
        textureController.GlowIntensity(distance, is_correct);
    }

    public void OnUpdateERDS(float[] values)
    {
        textureController.UpdateERDSValues(values);
    }
}
